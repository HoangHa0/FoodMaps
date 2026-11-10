/**
 * The ONE API client of the frontend, typed from the backend schema (openapi.json -> schema.d.ts).
 * Do not hand-write fetch("/api/...") in features: backend schema changes would go unnoticed.
 *
 *   const { data, error } = await api.POST("/api/auth/login", { body: { username, password } });
 *
 * After a backend schema change: run `make api-types`, then commit openapi.json + schema.d.ts.
 */
import createClient from "openapi-fetch";

import { ApiError } from "./errors";
import type { components, paths } from "./schema";

// A request that never answers must not leave a spinner forever: give up, and let TanStack Query
// retry reads. Writes get more time (the first AI Match search loads the model).
const READ_TIMEOUT_MS = 15_000;
const WRITE_TIMEOUT_MS = 60_000;

async function fetchWithTimeout(request: Request): Promise<Response> {
  const timeout = AbortSignal.timeout(request.method === "GET" ? READ_TIMEOUT_MS : WRITE_TIMEOUT_MS);
  const signal = typeof AbortSignal.any === "function" ? AbortSignal.any([request.signal, timeout]) : timeout;
  try {
    return await fetch(new Request(request, { signal }));
  } catch (e) {
    if (e instanceof DOMException && e.name === "TimeoutError") {
      throw new ApiError(0, "timeout", "Máy chủ phản hồi quá lâu. Bạn thử lại nhé.");
    }
    if (e instanceof DOMException && e.name === "AbortError") throw e; // cancelled on purpose
    throw new ApiError(0, "network_error", "Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại.");
  }
}

export const api = createClient<paths>({ baseUrl: "", credentials: "same-origin", fetch: fetchWithTimeout });

export type Schemas = components["schemas"];
