import type { NextConfig } from "next";

// Every /api/* request is proxied by Next.js to FastAPI, so the browser only ever sees ONE
// origin: the httpOnly session cookie works without CORS, and the backend URL stays private.
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  // Stop `next dev` from generating AGENTS.md / CLAUDE.md when it detects an AI coding tool.
  agentRules: false,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND_URL}/api/:path*` }];
  },
};

export default nextConfig;
