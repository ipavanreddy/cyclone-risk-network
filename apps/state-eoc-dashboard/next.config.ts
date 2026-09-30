import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Cloud Run image: self-contained server (infrastructure/cloud-run/Dockerfile.web)
  output: "standalone",
  // pnpm workspace: trace files from the repo root so the standalone bundle includes hoisted deps
  outputFileTracingRoot: path.join(__dirname, "../.."),
};

export default nextConfig;
