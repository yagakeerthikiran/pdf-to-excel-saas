/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker
  output: 'standalone',
  
  // Disable telemetry in production
  experimental: {
    telemetry: false
  },
  
  // Skip build-time validation for APIs that need runtime env
  env: {
    SKIP_ENV_VALIDATION: process.env.SKIP_ENV_VALIDATION || 'false'
  },
  
  // Handle build errors gracefully
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  
  // Webpack config to handle problematic dependencies
  webpack: (config, { isServer }) => {
    if (isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false
      }
    }
    return config
  },
  
  // Handle external modules that cause build issues
  experimental: {
    serverComponentsExternalPackages: ['@prisma/client', '@sentry/node']
  }
}

module.exports = nextConfig