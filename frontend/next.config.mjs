/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: process.env.BUILD_TARGET === 'mobile' ? 'export' : 'standalone',
};

export default nextConfig;
