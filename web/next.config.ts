import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [{ source: "/api/:path*", destination: "http://api:8000/:path*" }];
  },
  eslint: {
    // Allow production builds to complete even with ESLint errors:
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
