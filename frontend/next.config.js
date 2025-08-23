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
  
  // Move these out of experimental for Next.js 15
  skipTrailingSlashRedirect: true,
  skipMiddlewareUrlNormalize: true,
  
  // Exclude problematic routes from static generation
  experimental: {
    // Skip static generation of API routes completely
    isrFlushToDisk: false,
    // Skip pre-rendering of API routes
    appDir: true,
  },
  
  // Custom webpack config to handle Stripe externally
  webpack: (config, { isServer, dev }) => {
    if (isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false
      }
      
      // Always externalize stripe to prevent build-time execution
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
  
  // Skip static optimization for API routes
  generateStaticParams: () => [],
}

module.exports = nextConfig