"""Minimal Groq client for the offline insights job. Uses `httpx` (already a dependency), so no new
package. Groq's API is OpenAI-compatible: one POST to `/chat/completions`.

The free tier is tight (see DECISIONS D13): about 8K tokens per MINUTE, 200K per DAY, 30 requests
per minute, 1K per day. This client therefore

- spaces requests so that the tokens of the last 60 seconds never exceed the per-minute limit
  (`TokenWindow`, driven by the token counts Groq reports back),
- waits and retries when Groq answers 429 with a short `retry-after`,
- raises `GroqQuotaExhausted` when the DAILY limit is hit, so the job can stop cleanly and be
  run again tomorrow (finished places are already saved).

Time and sleeping are injected, so the pacing logic is unit tested without waiting.
"""

import asyncio
import json
import re
import time
from collections import deque
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass

import httpx

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

TPM_LIMIT = 8_000  # free-tier tokens per minute for gpt-oss models
TPM_MARGIN = 500  # stay below the limit: our token estimate is not exact
WINDOW_SECONDS = 60.0

MAX_ATTEMPTS = 4
MAX_RETRY_WAIT_S = 180.0  # a longer wait than this means a daily limit, not a per-minute one
DEFAULT_RETRY_WAIT_S = 30.0
REQUEST_TIMEOUT_S = 90.0


class GroqError(RuntimeError):
    """The request failed and retrying will not help (bad key, bad request, repeated failures)."""


class GroqQuotaExhausted(GroqError):
    """The daily token/request limit is used up. Finished work is saved: run the job again later."""


@dataclass(frozen=True)
class ChatReply:
    content: str
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


# --------------------------------------------------------------------------- pacing


class TokenWindow:
    """Remembers the tokens spent in the last 60 s, to know how long to wait before the next call."""

    def __init__(self, limit: int = TPM_LIMIT - TPM_MARGIN, window_s: float = WINDOW_SECONDS) -> None:
        self.limit = limit
        self.window_s = window_s
        self._spent: deque[tuple[float, int]] = deque()  # (time, tokens), oldest first

    def record(self, tokens: int, now: float) -> None:
        self._spent.append((now, tokens))

    def _drop_old(self, now: float) -> None:
        while self._spent and now - self._spent[0][0] >= self.window_s:
            self._spent.popleft()

    def wait_seconds(self, needed: int, now: float) -> float:
        """Seconds to wait before a request of about `needed` tokens fits in the window (0 = go)."""
        self._drop_old(now)
        total = sum(tokens for _, tokens in self._spent)
        if total + needed <= self.limit:
            return 0.0
        for when, tokens in self._spent:  # oldest first: when does enough room appear?
            total -= tokens
            if total + needed <= self.limit:
                return max(0.0, when + self.window_s - now)
        return 0.0  # the request alone is over the limit: let the API decide


# --------------------------------------------------------------------------- 429 handling


def is_daily_limit(message: str) -> bool:
    """True when Groq's error says the DAY limit is reached (tokens or requests per day)."""
    m = message.lower()
    return "per day" in m or "tpd" in m or "rpd" in m


def parse_retry_after(headers: Mapping[str, str]) -> float | None:
    """Seconds from a `retry-after` header, or None. Groq sends plain seconds (may be fractional)."""
    raw = headers.get("retry-after")
    if raw is None:
        return None
    try:
        return max(0.0, float(raw))
    except ValueError:
        return None


def _error_message(response: httpx.Response) -> str:
    try:
        return str(response.json()["error"]["message"])
    except (ValueError, KeyError, TypeError):
        return response.text[:300]


def reasoning_params(model: str) -> dict[str, object]:
    """Keep the model's hidden reasoning small: it costs output tokens and the quota is tiny."""
    name = model.lower()
    if "gpt-oss" in name:
        return {"reasoning_effort": "low", "include_reasoning": False}
    if "qwen3" in name:
        return {"reasoning_effort": "none"}
    return {}


# --------------------------------------------------------------------------- client


class GroqClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        http: httpx.AsyncClient | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        clock: Callable[[], float] = time.monotonic,
        on_wait: Callable[[float, str], None] | None = None,
    ) -> None:
        if not api_key:
            raise GroqError("Thiếu GROQ_API_KEY (đặt trong backend/.env)")
        self.model = model
        self._api_key = api_key
        self._http = http or httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S)
        self._owns_http = http is None
        self._sleep = sleep
        self._clock = clock
        self._on_wait = on_wait or (lambda _seconds, _why: None)
        self.window = TokenWindow()

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def _wait(self, seconds: float, why: str) -> None:
        if seconds > 0:
            self._on_wait(seconds, why)
            await self._sleep(seconds)

    async def chat_json(self, system: str, user: str, *, max_tokens: int, estimated_prompt: int) -> ChatReply:
        """One chat completion that must be a JSON object. `estimated_prompt` is only for pacing."""
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.2,
            "max_completion_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            **reasoning_params(self.model),
        }
        needed = estimated_prompt + max_tokens  # Groq counts the requested output as well
        last_error = "không rõ"

        for attempt in range(1, MAX_ATTEMPTS + 1):
            await self._wait(self.window.wait_seconds(needed, self._clock()), "đợi hạn mức token/phút")
            try:
                response = await self._http.post(
                    GROQ_URL, json=payload, headers={"Authorization": f"Bearer {self._api_key}"}
                )
            except httpx.TransportError as e:
                last_error = f"lỗi mạng ({type(e).__name__})"
                await self._wait(2.0**attempt, "lỗi mạng, thử lại")
                continue

            if response.status_code == 429:
                message = _error_message(response)
                wait = parse_retry_after(response.headers)
                if is_daily_limit(message) or (wait is not None and wait > MAX_RETRY_WAIT_S):
                    raise GroqQuotaExhausted(message)
                last_error = f"429: {message}"
                await self._wait(
                    (wait if wait is not None else DEFAULT_RETRY_WAIT_S) + 1.0, "bị giới hạn, chờ"
                )
                continue
            if response.status_code in (401, 403):
                raise GroqError(f"Groq từ chối API key ({response.status_code}): {_error_message(response)}")
            if response.status_code >= 500:
                last_error = f"{response.status_code}: {_error_message(response)}"
                await self._wait(2.0**attempt, "Groq lỗi phía server, thử lại")
                continue
            if response.status_code >= 400:
                raise GroqError(f"Groq báo lỗi {response.status_code}: {_error_message(response)}")

            return self._read_reply(response)

        raise GroqError(f"Groq lỗi sau {MAX_ATTEMPTS} lần thử (lần cuối: {last_error})")

    def _read_reply(self, response: httpx.Response) -> ChatReply:
        try:
            data = response.json()
            choice = data["choices"][0]
            content = strip_reasoning(choice["message"]["content"] or "")
            usage = data.get("usage") or {}
            reply = ChatReply(
                content=content,
                prompt_tokens=int(usage.get("prompt_tokens", 0)),
                completion_tokens=int(usage.get("completion_tokens", 0)),
            )
        except (ValueError, KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
            raise GroqError(f"Groq trả về dữ liệu lạ: {e}") from None
        self.window.record(reply.total_tokens, self._clock())
        if choice.get("finish_reason") == "length":
            raise GroqError("Câu trả lời bị cắt vì hết max_tokens (JSON không đầy đủ)")
        return reply


def strip_reasoning(text: str) -> str:
    """Some models put <think>...</think> before the JSON; the JSON parser must not see it."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
