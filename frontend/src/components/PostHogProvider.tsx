'use client'
import posthog from 'posthog-js'
import { PostHogProvider as PHProvider } from 'posthog-js/react'
import { useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'

if (typeof window !== 'undefined') {
  posthog.init(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
    // Enable debug mode in development
    loaded: (posthog) => {
      if (process.env.NODE_ENV === 'development') posthog.debug()
    }
  })
}

function PostHogAuthWrapper({ children }: { children: React.ReactNode }) {
  const supabase = createClient()

  useEffect(() => {
    const getAndIdentifyUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        posthog.identify(user.id, {
          email: user.email,
        });
      } else {
        posthog.reset();
      }
    };
    getAndIdentifyUser();

    const { data: authListener } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN' && session?.user) {
        posthog.identify(session.user.id, {
          email: session.user.email,
        });
      } else if (event === 'SIGNED_OUT') {
        posthog.reset();
      }
    });

    return () => {
      authListener.subscription.unsubscribe();
    };
  }, [supabase]);

  return <>{children}</>;
}


export default function PostHogProvider({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <PHProvider client={posthog}>
      <PostHogAuthWrapper>
        {children}
      </PostHogAuthWrapper>
    </PHProvider>
  )
}
