const nextConfig = {
  output: "standalone",
  async rewrites() {
    const configured = process.env.API_INTERNAL_URL || "http://localhost:8000";
    const backend = configured.startsWith("http") ? configured : "https://" + configured;
    const base = backend.replace(/\/$/, "");
    return [
      { source: "/api/:path*", destination: base + "/api/:path*" },
      { source: "/health", destination: base + "/health" }
    ];
  }
};
export default nextConfig;
