'use client'

import { useState, useEffect } from 'react'
import { createClientComponentClient } from '@/lib/supabase'
import { apiClient } from '@/lib/api'
import PdfUpload from './PdfUpload'

interface UserProfile {
  id: string
  email: string
  subscription_tier: string
  conversions_remaining: number
  created_at: string
}

interface Conversion {
  id: string
  filename: string
  status: string
  created_at: string
  download_url?: string
}

export default function Dashboard() {
  const [user, setUser] = useState(null)
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [conversions, setConversions] = useState<Conversion[]>([])
  const [activeTab, setActiveTab] = useState<'upload' | 'history' | 'settings'>('upload')
  const [isLoading, setIsLoading] = useState(true)
  const [isCancelling, setIsCancelling] = useState(false)
  
  const supabase = createClientComponentClient()

  useEffect(() => {
    const initialize = async () => {
      try {
        // Check auth status
        const { data: { user } } = await supabase.auth.getUser()
        if (!user) {
          window.location.href = '/auth/signin'
          return
        }
        
        setUser(user)
        
        // Load profile and conversions
        const [profileData, conversionsData] = await Promise.all([
          apiClient.getProfile().catch(() => null),
          apiClient.getConversions().catch(() => [])
        ])
        
        setProfile(profileData)
        setConversions(conversionsData)
      } catch (error) {
        console.error('Dashboard initialization failed:', error)
      } finally {
        setIsLoading(false)
      }
    }

    initialize()
  }, [supabase])

  const handleSignOut = async () => {
    await supabase.auth.signOut()
    window.location.href = '/'
  }

  const handleCancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription? You\'ll lose Pro features at the end of your billing period.')) {
      return
    }

    setIsCancelling(true)
    try {
      await apiClient.cancelSubscription()
      alert('Subscription cancelled successfully. You\'ll continue to have Pro access until the end of your billing period.')
      
      // Refresh profile
      const profileData = await apiClient.getProfile()
      setProfile(profileData)
    } catch (error: any) {
      alert(`Failed to cancel subscription: ${error.message}`)
    } finally {
      setIsCancelling(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-AU', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    )
  }

  const isPro = profile?.subscription_tier === 'pro'
  const remainingConversions = profile?.conversions_remaining || 0

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">
                PDF to Excel Dashboard
              </h1>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                isPro 
                  ? 'bg-blue-100 text-blue-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {isPro ? 'Pro' : 'Free'} Plan
              </span>
            </div>

            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                <span className="font-medium">{remainingConversions}</span> conversions left
              </div>
              
              <button
                onClick={handleSignOut}
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            {[
              { key: 'upload', label: 'Convert PDFs', icon: '📄' },
              { key: 'history', label: 'History', icon: '📊' },
              { key: 'settings', label: 'Settings', icon: '⚙️' }
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Usage Warning */}
        {remainingConversions <= 5 && remainingConversions > 0 && (
          <div className="mb-8 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center">
              <span className="text-yellow-600 mr-3">⚠️</span>
              <div className="flex-1">
                <h3 className="text-sm font-medium text-yellow-800">
                  Running Low on Conversions
                </h3>
                <p className="text-sm text-yellow-700 mt-1">
                  You have {remainingConversions} conversions left. 
                  {!isPro && (
                    <span>
                      {' '}
                      <a href="/pricing" className="font-medium underline hover:no-underline">
                        Upgrade to Pro
                      </a>
                      {' '}for unlimited conversions.
                    </span>
                  )}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* No conversions left */}
        {remainingConversions === 0 && (
          <div className="mb-8 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <span className="text-red-600 mr-3">🚫</span>
              <div className="flex-1">
                <h3 className="text-sm font-medium text-red-800">
                  No Conversions Remaining
                </h3>
                <p className="text-sm text-red-700 mt-1">
                  You've used all your conversions for this month. 
                  <a href="/pricing" className="font-medium underline hover:no-underline ml-1">
                    Upgrade to Pro
                  </a>
                  {' '}to continue converting PDFs.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tab Content */}
        {activeTab === 'upload' && (
          <div>
            {remainingConversions > 0 ? (
              <PdfUpload />
            ) : (
              <div className="text-center py-12">
                <p className="text-gray-600 mb-4">
                  You need more conversions to upload files.
                </p>
                <a
                  href="/pricing"
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  View Pricing Plans
                </a>
              </div>
            )}
          </div>
        )}

        {activeTab === 'history' && (
          <div>
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="px-6 py-4 border-b">
                <h2 className="text-lg font-semibold text-gray-900">
                  Conversion History
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  Your recent PDF to Excel conversions
                </p>
              </div>

              {conversions.length === 0 ? (
                <div className="px-6 py-12 text-center">
                  <div className="text-gray-400 mb-4">
                    <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-sm font-medium text-gray-900 mb-1">
                    No conversions yet
                  </h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Start by converting your first PDF to Excel
                  </p>
                  <button
                    onClick={() => setActiveTab('upload')}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                  >
                    Convert Your First PDF
                  </button>
                </div>
              ) : (
                <div className="divide-y">
                  {conversions.map((conversion) => (
                    <div key={conversion.id} className="px-6 py-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className={`w-3 h-3 rounded-full ${
                            conversion.status === 'completed' ? 'bg-green-400' :
                            conversion.status === 'processing' ? 'bg-yellow-400' :
                            conversion.status === 'failed' ? 'bg-red-400' :
                            'bg-gray-400'
                          }`} />
                          
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {conversion.filename}
                            </p>
                            <p className="text-xs text-gray-600">
                              {formatDate(conversion.created_at)} • Status: {conversion.status}
                            </p>
                          </div>
                        </div>

                        {conversion.status === 'completed' && conversion.download_url && (
                          <a
                            href={conversion.download_url}
                            download
                            className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700"
                          >
                            Download
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="space-y-6">
            {/* Account Information */}
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="px-6 py-4 border-b">
                <h2 className="text-lg font-semibold text-gray-900">
                  Account Information
                </h2>
              </div>
              
              <div className="px-6 py-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Email Address
                  </label>
                  <p className="mt-1 text-sm text-gray-900">
                    {user?.email}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Account Created
                  </label>
                  <p className="mt-1 text-sm text-gray-900">
                    {profile?.created_at ? formatDate(profile.created_at) : 'Unknown'}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Current Plan
                  </label>
                  <div className="mt-1 flex items-center space-x-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      isPro 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {isPro ? 'Professional' : 'Free'}
                    </span>
                    
                    {!isPro && (
                      <a
                        href="/pricing"
                        className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                      >
                        Upgrade to Pro
                      </a>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Conversions Remaining
                  </label>
                  <p className="mt-1 text-sm text-gray-900">
                    {remainingConversions} conversions left this month
                  </p>
                </div>
              </div>
            </div>

            {/* Subscription Management */}
            {isPro && (
              <div className="bg-white rounded-lg shadow-sm border">
                <div className="px-6 py-4 border-b">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Subscription Management
                  </h2>
                </div>
                
                <div className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">
                        Professional Plan
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">
                        $29/month • 500 conversions per month
                      </p>
                    </div>

                    <button
                      onClick={handleCancelSubscription}
                      disabled={isCancelling}
                      className="px-4 py-2 border border-red-300 text-sm font-medium text-red-700 bg-white hover:bg-red-50 rounded-md disabled:opacity-50"
                    >
                      {isCancelling ? 'Cancelling...' : 'Cancel Subscription'}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Danger Zone */}
            <div className="bg-white rounded-lg shadow-sm border border-red-200">
              <div className="px-6 py-4 border-b border-red-200">
                <h2 className="text-lg font-semibold text-red-900">
                  Danger Zone
                </h2>
              </div>
              
              <div className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-red-900">
                      Delete Account
                    </h3>
                    <p className="text-sm text-red-700 mt-1">
                      Permanently delete your account and all associated data.
                    </p>
                  </div>

                  <button
                    onClick={() => {
                      alert('Account deletion is not implemented yet. Please contact support.')
                    }}
                    className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700"
                  >
                    Delete Account
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
