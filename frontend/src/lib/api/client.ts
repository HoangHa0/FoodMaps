/**
 * The ONE API client of the frontend, typed from the backend schema (openapi.json -> schema.d.ts).
 * Do not hand-write fetch("/api/...") in features: backend schema changes would go unnoticed.
 *
 *   const { data, error } = await api.POST("/api/auth/login", { body: { username, password } });
 *
 * After a backend schema change: run `make api-types`, then commit openapi.json + schema.d.ts.
 */
import createClient from "openapi-fetch";

import type { components, paths } from "./schema";

export const api = createClient<paths>({ baseUrl: "", credentials: "same-origin" });

export type Schemas = components["schemas"];
