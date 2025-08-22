/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // Remove the deprecated experimental option
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
}

module.exports = nextConfig