import { ApiError } from "@/lib/api/errors";

/** The server's Vietnamese message when there is one, otherwise a generic line. */
export function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Có lỗi xảy ra, thử lại sau";
}