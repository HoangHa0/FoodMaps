/** The backend always returns errors as {"error": {"code", "message"}} (backend/app/core/errors.py). */
export interface ApiErrorBody {
  error?: { code: string; message: string };
  detail?: unknown; // FastAPI's default 422 validation error
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

/** Turns an openapi-fetch result into data, or throws ApiError. Use inside queryFn / mutationFn. */
export function unwrap<T>(res: { data?: T; error?: unknown; response: Response }): T {
  if (res.error !== undefined || !res.response.ok) {
    const body = (res.error ?? {}) as ApiErrorBody;
    const code = body.error?.code ?? (res.response.status === 422 ? "validation_error" : "unknown");
    const message = body.error?.message ?? "Có lỗi xảy ra, thử lại sau";
    throw new ApiError(res.response.status, code, message);
  }
  return res.data as T;
}
