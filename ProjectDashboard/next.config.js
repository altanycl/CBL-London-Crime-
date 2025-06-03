/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  typescript: {
    // !! WARN !!
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors.
    // !! WARN !!
    ignoreBuildErrors: true,
  },
  // Server configuration - change the port if needed
  serverRuntimeConfig: {
    port: process.env.PORT || 4000,
  },
};

module.exports = nextConfig; 