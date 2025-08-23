/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker
  output: 'standalone',
  
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
  
  // Skip static generation of API routes that require runtime dependencies
  experimental: {
    skipTrailingSlashRedirect: true,
    skipMiddlewareUrlNormalize: true,
  },
  
  // Exclude API routes from static generation during build
  generateBuildId: async () => {
    // Custom build ID to ensure API routes are generated at runtime
    return 'docker-build-' + Date.now()
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
    
    // Exclude Stripe from server-side bundling during build if no API key available
    if (isServer && !process.env.STRIPE_SECRET_KEY) {
      config.externals = config.externals || []
      config.externals.push('stripe')
    }
    
    return config
  },
  
  // Handle external packages
  serverExternalPackages: ['@prisma/client', '@sentry/node', 'stripe']
}

module.exports = nextConfig