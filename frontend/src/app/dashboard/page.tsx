'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import FileUpload from '@/components/FileUpload'
import { Elements, useStripe } from '@stripe/react-stripe-js'
import { getStripe } from '@/lib/stripe'
import { createClient } from '@/lib/supabase/client'
import type { User } from '@supabase/supabase-js'

const FREE_TIER_LIMIT = 5;

interface UsageData {
  free_conversions_used: number;
  subscription_status: 'free' | 'pro';
}

function DashboardContent() {
  const stripe = useStripe()
  const supabase = createClient()
  const [user, setUser] = useState<User | null>(null)
  const [usage, setUsage] = useState<UsageData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const getUserAndUsage = async () => {
      setLoading(true);
      const { data: { user } } = await supabase.auth.getUser();
      setUser(user);

      if (user) {
        try {
          const res = await fetch('/api/usage', {
            headers: { 'X-User-ID': user.id }
          });
          if (res.ok) {
            const usageData = await res.json();
            setUsage(usageData);
          }
        } catch (error) {
          console.error("Failed to fetch usage data", error);
        }
      }
      setLoading(false);
    }
    getUserAndUsage()
  }, [supabase])

  const handleUpgrade = async () => {
    if (!user) return alert('You must be logged in to upgrade.');
    try {
      const priceId = process.env.NEXT_PUBLIC_STRIPE_MONTHLY_PRICE_ID!;
      const res = await fetch('/api/create-checkout-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-ID': user.id },
        body: JSON.stringify({ price_id: priceId, user_id: user.id }),
      });
      if (!res.ok) throw new Error('Failed to create checkout session.');
      const { session_id } = await res.json();
      if (!stripe) throw new Error('Stripe.js has not loaded yet.');
      const { error } = await stripe.redirectToCheckout({ sessionId: session_id });
      if (error) alert(error.message);
    } catch (error) {
      console.error(error);
      alert(error instanceof Error ? error.message : 'An unknown error occurred.');
    }
  };

  if (loading) {
    return <div className="text-center p-24">Loading...</div>;
  }

  if (!user) {
    return (
      <div className="text-center p-24">
        <h1 className="text-4xl font-bold">Access Denied</h1>
        <p className="mt-4 text-lg">Please{' '}
          <Link href="/auth" className="text-blue-600 hover:underline">
            sign in
          </Link>
          {' '}to access your dashboard.
        </p>
      </div>
    );
  }

  const conversionsLeft = usage ? FREE_TIER_LIMIT - usage.free_conversions_used : 0;
  const hasReachedLimit = usage?.subscription_status === 'free' && conversionsLeft <= 0;

  return (
    <div className="w-full max-w-lg text-center">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold">Dashboard</h1>
        <button
          onClick={handleUpgrade}
          className="px-4 py-2 font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700"
        >
          Upgrade to Pro
        </button>
      </div>
      <p className="mt-4 text-lg">
        Welcome, {user.email}.
      </p>

      {usage && usage.subscription_status === 'free' && (
        <p className="mt-2 text-md text-gray-600">
          You have {Math.max(0, conversionsLeft)} free conversions remaining.
        </p>
      )}

      <div className="mt-8">
        {hasReachedLimit ? (
          <div className="p-4 bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700">
            <p className="font-bold">Free Limit Reached</p>
            <p>You have used all your free conversions. Please upgrade to Pro to continue.</p>
          </div>
        ) : (
          <FileUpload user={user} />
        )}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const stripePromise = getStripe();
  return (
    <div className="flex min-h-screen flex-col items-center justify-center">
      <Elements stripe={stripePromise}>
        <DashboardContent />
      </Elements>
    </div>
  )
}
