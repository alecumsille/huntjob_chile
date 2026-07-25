import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  serverExternalPackages: [],
  allowedDevOrigins: [
    "bsxuh-2803-c600-f102-aec7-97d1-b79a-972-afb6.free.pinggy.net",
    "jiuem-2803-c600-f102-aec7-97d1-b79a-972-afb6.run.pinggy-free.link",
    "ixogb-2803-c600-f102-aec7-80e3-5518-1952-19f5.free.pinggy.net",
    "ixogb-2803-c600-f102-aec7-80e3-5518-1952-19f5.run.pinggy-free.link"
  ],
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  experimental: {
    turbopack: {
      root: path.join(process.cwd(), ".."),
    },
  },
};

export default nextConfig;
