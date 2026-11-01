const nextConfig = {
  output: "standalone",
  async rewrites() {
    const backend = process.env.API_INTERNAL_URL || "http://localhost:8000";
    return [{source:"/api/:path*",destination:backend+"/api/:path*"},
            {source:"/health",destination:backend+"/health"}];
  }
};
export default nextConfig;
