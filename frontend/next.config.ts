import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  /* config options here */
  typescript: {
    ignoreBuildErrors: true,
  },
  reactStrictMode: false,
  devIndicators: false,
  async rewrites() {
    return [
      {
        source: '/api/python/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
      {
        source: '/api/chat',
        destination: 'http://localhost:8000/api/_projectX/chat',
      },
      {
        source: '/api/decision',
        destination: 'http://localhost:8000/api/_projectX/decision',
      },
      {
        source: '/api/fuzz',
        destination: 'http://localhost:8000/api/_projectX/fuzz',
      },
      {
        source: '/api/health',
        destination: 'http://localhost:8000/api/_projectX/health',
      },
      {
        source: '/api/hook',
        destination: 'http://localhost:8000/api/_projectX/hook',
      },
      {
        source: '/api/pay/confirm',
        destination: 'http://localhost:8000/api/_projectX/pay/confirm',
      },
      {
        source: '/api/reset',
        destination: 'http://localhost:8000/api/_projectX/reset',
      },
      {
        source: '/api/state',
        destination: 'http://localhost:8000/api/_projectX/state',
      },
      {
        source: '/api/trace/:id',
        destination: 'http://localhost:8000/api/_projectX/trace/:id',
      },
    ];
  },
};

export default nextConfig;
