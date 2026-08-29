/** @type {import('next').NextConfig} */
const API_BASE = process.env.FLOODGUARD_API_BASE ?? 'http://localhost:8000';

const nextConfig = {
  reactStrictMode: true,

  // Every browser request goes to /api/... on this origin and is rewritten to the
  // FastAPI gateway. That keeps the API base out of client bundles, removes CORS from
  // the picture entirely, and means only one hostname changes when we deploy.
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${API_BASE}/:path*` }];
  },
};

export default nextConfig;
