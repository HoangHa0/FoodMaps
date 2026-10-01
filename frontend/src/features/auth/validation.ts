/** Same rules as backend/app/modules/auth/schemas.py: change both together. */
export const USERNAME_RE = /^[A-Za-z0-9_.]{3,30}$/;

export function validateUsername(u: string): string | undefined {
  return USERNAME_RE.test(u) ? undefined : "3-30 ký tự, chỉ gồm chữ không dấu, số, _ và .";
}

export function validatePassword(p: string): string | undefined {
  if (p.length < 8) return "Mật khẩu tối thiểu 8 ký tự";
  // bcrypt limit is 72 BYTES; accented letters take 2-3 bytes in UTF-8
  if (new TextEncoder().encode(p).length > 72) return "Mật khẩu quá dài";
  return undefined;
}

/** Only follow ?next= to a path on this site (blocks "https://evil.com" and "//evil.com"). */
export function safeNext(next: string | null): string {
  return next && next.startsWith("/") && !next.startsWith("//") ? next : "/";
}
