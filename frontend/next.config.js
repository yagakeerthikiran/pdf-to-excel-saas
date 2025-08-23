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
  
  // Next.js 15 options (moved out of experimental)
  skipTrailingSlashRedirect: true,
  skipMiddlewareUrlNormalize: true,
  
  // Custom webpack config to handle external packages
  webpack: (config, { isServer }) => {
    if (isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false
      }
      
      // Externalize packages that should not be bundled
      config.externals = config.externals || []
      if (Array.isArray(config.externals)) {
        config.externals.push('stripe')
      } else {
        config.externals = [config.externals, 'stripe']
      }
    }
    
    return config
  },
  
  // Handle external packages that shouldn't be bundled
  serverExternalPackages: ['@prisma/client', '@sentry/node', 'stripe'],
}

module.exports = nextConfig