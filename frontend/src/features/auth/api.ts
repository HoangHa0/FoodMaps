import { api, type Schemas } from "@/lib/api/client";
import { unwrap } from "@/lib/api/errors";

/** M1 API calls. Hooks and components never call `api.*` directly. */
export const authApi = {
  me: async () => {
    const res = await api.GET("/api/auth/me");
    if (res.response.status === 401) return null; // guest
    return unwrap(res);
  },
  // M1: login, register, logout, e.g. unwrap(await api.POST("/api/auth/login", { body }))
  login: async (body: Schemas["LoginIn"]) => unwrap(await api.POST("/api/auth/login", { body })),
  register: async (body: Schemas["RegisterIn"]) => unwrap(await api.POST("/api/auth/register", { body })),
  logout: async () => {
    unwrap(await api.POST("/api/auth/logout"));
  },
};
