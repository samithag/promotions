import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Bundle a minimal server and only the files it needs, for the Docker image.
  output: "standalone",
};

export default nextConfig;
