'use client'
import { useEffect } from 'react'
import posthog from 'posthog-js'

export function ClientProviders({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const postHogKey = process.env.NEXT_PUBLIC_POSTHOG_KEY
      const postHogHost = process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://us.i.posthog.com'
      
      // Only initialize PostHog if we have a valid key
      if (postHogKey && postHogKey.startsWith('phc_')) {
        try {
          posthog.init(postHogKey, {
            api_host: postHogHost,
            person_profiles: 'identified_only',
            loaded: (posthog) => {
              if (process.env.NODE_ENV === 'development') {
                console.log('PostHog initialized successfully')
              }
            }
          })
        } catch (error) {
          console.warn('PostHog initialization failed:', error)
        }
      } else {
        console.warn('PostHog not initialized: Missing or invalid NEXT_PUBLIC_POSTHOG_KEY')
        // Create a mock posthog object to prevent errors
        window.posthog = {
          capture: () => {},
          identify: () => {},
          reset: () => {},
          debug: () => {}
        }
      }
    }
  }, [])

  return <>{children}</>
}

export default ClientProviders