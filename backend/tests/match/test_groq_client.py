"""Groq client: pacing and error handling, with a fake HTTP transport and a fake clock (no waiting)."""

import json

import httpx
import pytest

from app.modules.match import groq_client as gc
from app.modules.match.groq_client import GroqClient, GroqError, GroqQuotaExhausted, TokenWindow


class Clock:
    """A fake clock whose `sleep` just moves time forward."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.slept: list[float] = []

    def __call__(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


def ok_response(content='{"summary": "x"}', prompt=3000, completion=700, finish="stop") -> httpx.Response:
    body = {
        "choices": [{"message": {"content": content}, "finish_reason": finish}],
        "usage": {"prompt_tokens": prompt, "completion_tokens": completion},
    }
    return httpx.Response(200, json=body)


def error_response(status: int, message: str, **headers) -> httpx.Response:
    return httpx.Response(status, json={"error": {"message": message}}, headers=headers)


def make_client(responses, clock=None, model="openai/gpt-oss-20b", waits=None):
    """A client whose server replays `responses` in order (an exception in the list is raised)."""
    clock = clock or Clock()
    seen: list[httpx.Request] = []
    queue = list(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    on_wait = (lambda s, why: waits.append((s, why))) if waits is not None else None
    client = GroqClient("test-key", model, http=http, sleep=clock.sleep, clock=clock, on_wait=on_wait)
    return client, clock, seen


async def call(client, **kw):
    return await client.chat_json("system", "user", max_tokens=2000, estimated_prompt=3000, **kw)


# --------------------------------------------------------------------------- TokenWindow


def test_window_allows_a_request_that_fits():
    w = TokenWindow(limit=7500)
    assert w.wait_seconds(5000, now=0) == 0
    w.record(2000, now=0)
    assert w.wait_seconds(5000, now=1) == 0  # 2000 + 5000 <= 7500


def test_window_waits_until_the_old_tokens_leave_the_minute():
    w = TokenWindow(limit=7500)
    w.record(6000, now=100)
    assert w.wait_seconds(5000, now=110) == pytest.approx(50)  # 6000 leaves the window at t = 160
    assert w.wait_seconds(5000, now=160) == 0


def test_window_waits_only_as_long_as_needed():
    w = TokenWindow(limit=7500)
    w.record(4000, now=0)
    w.record(3000, now=30)
    # 7000 spent; a 3000-token request needs the first 4000 to leave -> at t = 60
    assert w.wait_seconds(3000, now=40) == pytest.approx(20)


def test_window_with_an_oversized_request_does_not_wait_forever():
    assert TokenWindow(limit=7500).wait_seconds(9000, now=0) == 0


# --------------------------------------------------------------------------- helpers


def test_daily_limit_detection():
    assert gc.is_daily_limit("Rate limit reached ... on tokens per day (TPD): Limit 200000")
    assert gc.is_daily_limit("... requests per day (RPD) ...")
    assert not gc.is_daily_limit("Rate limit reached ... on tokens per minute (TPM): Limit 8000")


def test_parse_retry_after():
    assert gc.parse_retry_after({"retry-after": "12"}) == 12
    assert gc.parse_retry_after({"retry-after": "2.5"}) == 2.5
    assert gc.parse_retry_after({"retry-after": "soon"}) is None
    assert gc.parse_retry_after({}) is None


def test_reasoning_is_kept_small_per_model_family():
    oss = gc.reasoning_params("openai/gpt-oss-20b")
    assert oss == {"reasoning_effort": "low", "include_reasoning": False}
    assert gc.reasoning_params("qwen/qwen3.6-27b") == {"reasoning_effort": "none"}
    assert gc.reasoning_params("llama-3.3-70b-versatile") == {}


def test_strip_reasoning():
    assert gc.strip_reasoning('<think>hmm</think>\n{"a": 1}') == '{"a": 1}'
    assert gc.strip_reasoning('{"a": 1}') == '{"a": 1}'


def test_a_missing_api_key_is_reported_before_any_request():
    with pytest.raises(GroqError, match="GROQ_API_KEY"):
        GroqClient("", "m")


# --------------------------------------------------------------------------- the request


async def test_success_returns_content_and_usage_and_sends_the_expected_request():
    client, _, seen = make_client([ok_response(prompt=3000, completion=700)])
    reply = await call(client)

    assert reply.content == '{"summary": "x"}'
    assert (reply.prompt_tokens, reply.completion_tokens, reply.total_tokens) == (3000, 700, 3700)

    req = seen[0]
    assert req.url == httpx.URL(gc.GROQ_URL)
    assert req.headers["authorization"] == "Bearer test-key"
    body = json.loads(req.content)
    assert body["model"] == "openai/gpt-oss-20b"
    assert body["response_format"] == {"type": "json_object"}
    assert body["max_completion_tokens"] == 2000
    assert body["reasoning_effort"] == "low" and body["include_reasoning"] is False
    assert [m["role"] for m in body["messages"]] == ["system", "user"]


async def test_the_second_request_waits_for_the_per_minute_budget():
    waits: list = []
    client, clock, _ = make_client([ok_response(prompt=4500, completion=1500), ok_response()], waits=waits)
    await call(client)  # 6000 tokens spent at t = 1000
    assert clock.slept == []
    await call(client)  # needs 5000 more: must wait for the first to leave the window
    assert clock.slept and clock.slept[0] == pytest.approx(60, abs=0.01)
    assert waits[0][1].startswith("đợi")


async def test_the_server_is_not_asked_again_when_the_budget_is_free():
    client, clock, seen = make_client([ok_response(prompt=100, completion=100), ok_response()])
    await call(client)
    await call(client)
    assert clock.slept == [] and len(seen) == 2


# --------------------------------------------------------------------------- errors


async def test_a_short_rate_limit_waits_and_retries():
    client, clock, seen = make_client(
        [error_response(429, "tokens per minute (TPM)", **{"retry-after": "7"}), ok_response()]
    )
    reply = await call(client)
    assert reply.content and len(seen) == 2
    assert clock.slept[0] == pytest.approx(8)  # retry-after + 1 s


async def test_the_daily_limit_raises_quota_exhausted_without_retrying():
    client, _, seen = make_client(
        [error_response(429, "Rate limit reached ... tokens per day (TPD): Limit 200000")]
    )
    with pytest.raises(GroqQuotaExhausted):
        await call(client)
    assert len(seen) == 1


async def test_a_very_long_retry_after_is_treated_as_a_daily_limit():
    client, _, _ = make_client([error_response(429, "limit", **{"retry-after": "3600"})])
    with pytest.raises(GroqQuotaExhausted):
        await call(client)


async def test_a_rejected_key_stops_at_once():
    client, _, seen = make_client([error_response(401, "Invalid API Key")])
    with pytest.raises(GroqError, match="API key") as e:
        await call(client)
    assert not isinstance(e.value, GroqQuotaExhausted) and len(seen) == 1


async def test_a_bad_request_is_not_retried():
    client, _, seen = make_client([error_response(400, "model not found")])
    with pytest.raises(GroqError, match="400"):
        await call(client)
    assert len(seen) == 1


async def test_server_errors_are_retried_then_give_up():
    client, clock, seen = make_client([error_response(503, "overloaded")] * gc.MAX_ATTEMPTS)
    with pytest.raises(GroqError, match="sau 4 lần"):
        await call(client)
    assert len(seen) == gc.MAX_ATTEMPTS and len(clock.slept) == gc.MAX_ATTEMPTS


async def test_a_network_error_is_retried():
    client, _, seen = make_client([httpx.ConnectError("boom"), ok_response()])
    assert (await call(client)).content
    assert len(seen) == 2


async def test_a_truncated_answer_is_an_error_but_its_tokens_still_count():
    client, _, _ = make_client([ok_response(finish="length", prompt=3000, completion=2000)])
    with pytest.raises(GroqError, match="max_tokens"):
        await call(client)
    assert client.window.wait_seconds(4000, client._clock()) > 0  # 5000 tokens were spent


async def test_a_strange_response_body_is_an_error():
    client, _, _ = make_client([httpx.Response(200, json={"unexpected": True})])
    with pytest.raises(GroqError, match="lạ"):
        await call(client)


async def test_think_tags_are_removed_from_the_content():
    client, _, _ = make_client([ok_response(content='<think>...</think>{"summary": "x"}')])
    assert (await call(client)).content == '{"summary": "x"}'
