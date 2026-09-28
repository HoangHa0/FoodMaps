#!/usr/bin/env node
/**
 * Regenerate the frontend API types from the backend schema (usually via `make api-types`):
 *   1. backend:  uv run python scripts/export_openapi.py ../frontend/openapi.json
 *   2. frontend: openapi-typescript openapi.json -o src/lib/api/schema.d.ts
 * Requires uv. Commit both generated files.
 */
import { execSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const frontend = join(dirname(fileURLToPath(import.meta.url)), "..");
const backend = join(frontend, "..", "backend");
const run = (cmd, cwd) => execSync(cmd, { cwd, stdio: "inherit", shell: true });

run(`uv run python scripts/export_openapi.py "${join(frontend, "openapi.json")}"`, backend);
run("npx openapi-typescript openapi.json -o src/lib/api/schema.d.ts", frontend);
