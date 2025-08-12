'use client'

import { createClient } from '@/lib/supabase/client'
import { Auth } from '@supabase/auth-ui-react'
import { ThemeSupa } from '@supabase/auth-ui-shared'

export default function AuthPage() {
  const supabase = createClient()

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="w-full max-w-md">
        <Auth
          supabaseClient={supabase}
          appearance={{ theme: ThemeSupa }}
          providers={['github', 'google']}
          redirectTo={`${process.env.NEXT_PUBLIC_BASE_URL}/auth/callback`}
        />
      </div>
    </div>
  )
}
