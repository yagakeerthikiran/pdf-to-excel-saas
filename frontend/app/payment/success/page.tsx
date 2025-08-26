'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

export default function PaymentSuccessPage() {
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Give a moment for Stripe webhook to process
    const timer = setTimeout(() => {
      setIsLoading(false)
    }, 3000)

    return () => clearTimeout(timer)
  }, [])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Processing your payment...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
        <div className="mb-6">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Payment Successful!
          </h1>
          
          <p className="text-gray-600">
            Welcome to PDF to Excel Pro! Your subscription is now active.
          </p>
        </div>

        <div className="bg-blue-50 rounded-lg p-4 mb-6">
          <h2 className="text-lg font-semibold text-blue-900 mb-2">
            What's Next?
          </h2>
          <ul className="text-sm text-blue-800 space-y-1 text-left">
            <li>✓ Access to 500 conversions per month</li>
            <li>✓ Advanced AI table detection</li>
            <li>✓ Premium OCR accuracy</li>
            <li>✓ Priority support</li>
            <li>✓ Bulk processing capabilities</li>
          </ul>
        </div>

        <div className="space-y-3">
          <Link
            href="/dashboard"
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium inline-block"
          >
            Go to Dashboard
          </Link>
          
          <Link
            href="/dashboard?tab=upload"
            className="w-full bg-gray-100 text-gray-700 py-3 px-4 rounded-lg hover:bg-gray-200 transition-colors font-medium inline-block"
          >
            Start Converting PDFs
          </Link>
        </div>

        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            You'll receive a confirmation email shortly. You can manage your subscription from your dashboard settings.
          </p>
        </div>
      </div>
    </div>
  )
}
