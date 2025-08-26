import { NextResponse } from 'next/server';

// Health check endpoint for load balancer and monitoring
export async function GET() {
  return NextResponse.json({
    status: 'healthy',
    service: 'pdf-excel-frontend',
    timestamp: new Date().toISOString(),
    version: process.env.npm_package_version || '1.0.0',
    environment: process.env.NODE_ENV || 'production',
    build: process.env.NEXT_PUBLIC_BUILD_ID || 'unknown'
  });
}
