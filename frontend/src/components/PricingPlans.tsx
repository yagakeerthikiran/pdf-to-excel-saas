'use client'

import { useState, useEffect } from 'react'
import { PLANS } from '@/lib/stripe'
import { apiClient } from '@/lib/api'
import { createClientComponentClient } from '@/lib/supabase'
import React from 'react'

export default function PricingPlans() {
  const [isLoading, setIsLoading] = useState<string | null>(null)
  const [user, setUser] = useState(null)
  
  const supabase = createClientComponentClient()

  // Check auth status
  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser()
      setUser(user)
    }
    getUser()
  }, [supabase])

  const handleSubscribe = async (planKey: string) => {
    if (planKey === 'FREE') {
      // Free plan - redirect to signup or dashboard
      if (user) {
        window.location.href = '/dashboard'
      } else {
        window.location.href = '/auth/signup'
      }
      return
    }

    if (!user) {
      // Redirect to sign up first
      window.location.href = '/auth/signup'
      return
    }

    setIsLoading(planKey)

    try {
      const plan = PLANS[planKey as keyof typeof PLANS]
      const response = await apiClient.createCheckoutSession(plan.priceId)
      window.location.href = response.checkout_url
    } catch (error: any) {
      console.error('Checkout failed:', error)
      alert('Failed to start checkout. Please try again.')
    } finally {
      setIsLoading(null)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-12">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Simple, Transparent Pricing
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Start with our free tier and upgrade when you need more conversions.
          No hidden fees, no surprises.
        </p>
      </div>

      {/* Pricing Cards */}
      <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
        {Object.entries(PLANS).map(([key, plan]) => (
          <div
            key={key}
            className={`rounded-lg border-2 p-8 relative ${
              key === 'PRO' 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-200 bg-white'
            }`}
          >
            {/* Popular badge */}
            {key === 'PRO' && (
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                <span className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                  Most Popular
                </span>
              </div>
            )}

            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                {plan.name}
              </h3>
              
              <div className="mb-4">
                <span className="text-4xl font-bold text-gray-900">
                  ${plan.price}
                </span>
                {plan.price > 0 && (
                  <span className="text-gray-600 ml-2">/month</span>
                )}
              </div>

              <p className="text-lg text-gray-600">
                {plan.conversions === 500 ? 'Up to' : ''} {plan.conversions} conversions
                {plan.price === 0 ? ' per month' : ' per month'}
              </p>
            </div>

            {/* Features */}
            <ul className="space-y-4 mb-8">
              {plan.features.map((feature, index) => (
                <li key={index} className="flex items-start">
                  <svg
                    className="h-6 w-6 text-green-500 flex-shrink-0 mr-3"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span className="text-gray-700">{feature}</span>
                </li>
              ))}
            </ul>

            {/* CTA Button */}
            <button
              onClick={() => handleSubscribe(key)}
              disabled={isLoading === key}
              className={`w-full py-3 px-6 rounded-lg font-semibold text-center transition-colors ${
                key === 'PRO'
                  ? 'bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50'
                  : 'bg-gray-100 text-gray-900 hover:bg-gray-200 disabled:opacity-50'
              }`}
            >
              {isLoading === key ? (
                'Loading...'
              ) : key === 'FREE' ? (
                user ? 'Current Plan' : 'Get Started Free'
              ) : (
                'Upgrade to Pro'
              )}
            </button>

            {key === 'PRO' && (
              <p className="text-xs text-gray-600 text-center mt-3">
                Cancel anytime. No long-term contracts.
              </p>
            )}
          </div>
        ))}
      </div>

      {/* FAQ Section */}
      <div className="mt-20">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Frequently Asked Questions
        </h2>
        
        <div className="max-w-3xl mx-auto space-y-8">
          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              What types of PDFs work best?
            </h3>
            <p className="text-gray-600">
              Our AI works with both text-based PDFs and scanned documents. For best results, 
              use PDFs with clear tables and readable text. We support complex tables, 
              merged cells, and multiple tables per page.
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              How accurate is the conversion?
            </h3>
            <p className="text-gray-600">
              Our Pro plan uses advanced AI with OCR capabilities, achieving 95%+ accuracy 
              on most documents. The free tier uses standard table detection with 
              85-90% accuracy on well-formatted PDFs.
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Is my data secure?
            </h3>
            <p className="text-gray-600">
              Yes! All files are processed securely and automatically deleted within 24 hours. 
              We use enterprise-grade encryption and comply with Australian privacy regulations.
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Can I cancel my subscription?
            </h3>
            <p className="text-gray-600">
              Absolutely! You can cancel your Pro subscription anytime from your account 
              settings. You'll continue to have Pro access until the end of your billing period, 
              then automatically switch to the free tier.
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm border">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Do you offer bulk processing?
            </h3>
            <p className="text-gray-600">
              Pro subscribers can upload multiple files at once and use our API for 
              bulk processing. Need higher volumes? Contact us for enterprise pricing.
            </p>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="mt-20 text-center bg-blue-600 rounded-lg p-12 text-white">
        <h2 className="text-3xl font-bold mb-4">
          Ready to Convert Your PDFs?
        </h2>
        <p className="text-xl mb-8 opacity-90">
          Join thousands of users who trust us with their document conversion needs.
        </p>
        <div className="space-x-4">
          <button
            onClick={() => handleSubscribe('FREE')}
            className="bg-white text-blue-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
          >
            Start Free Trial
          </button>
          <button
            onClick={() => handleSubscribe('PRO')}
            className="bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-800 transition-colors border border-blue-400"
          >
            Upgrade to Pro
          </button>
        </div>
      </div>
    </div>
  )
}
