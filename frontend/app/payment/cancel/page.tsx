import Link from 'next/link'

export default function PaymentCancelPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
        <div className="mb-6">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Payment Cancelled
          </h1>
          
          <p className="text-gray-600">
            No worries! Your payment was cancelled and no charges were made.
          </p>
        </div>

        <div className="bg-blue-50 rounded-lg p-4 mb-6">
          <h2 className="text-lg font-semibold text-blue-900 mb-2">
            Still want to upgrade?
          </h2>
          <p className="text-sm text-blue-800">
            You can still enjoy our free tier with 5 conversions per month, 
            or upgrade to Pro anytime for unlimited conversions.
          </p>
        </div>

        <div className="space-y-3">
          <Link
            href="/pricing"
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium inline-block"
          >
            View Pricing Plans
          </Link>
          
          <Link
            href="/dashboard"
            className="w-full bg-gray-100 text-gray-700 py-3 px-4 rounded-lg hover:bg-gray-200 transition-colors font-medium inline-block"
          >
            Go to Dashboard
          </Link>
          
          <Link
            href="/"
            className="w-full text-gray-500 py-3 px-4 rounded-lg hover:text-gray-700 transition-colors font-medium inline-block"
          >
            Back to Home
          </Link>
        </div>

        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            Need help? Contact our support team if you have any questions about our pricing or features.
          </p>
        </div>
      </div>
    </div>
  )
}
