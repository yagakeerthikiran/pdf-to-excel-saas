'use client'

import { useEffect, useState } from 'react'
import FileUpload from '@/components/FileUpload'
import { Elements, useStripe } from '@stripe/react-stripe-js'
import { getStripe } from '@/lib/stripe'
import { createClient } from '@/lib/supabase/client'
import type { User } from '@supabase/supabase-js'

function DashboardContent() {
  const stripe = useStripe()
  const supabase = createClient()
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      setUser(user);
    }
    getUser()
  }, [supabase])

  const handleUpgrade = async () => {
    if (!user) {
      alert('You must be logged in to upgrade.');
      return;
    }

    try {
      const priceId = process.env.NEXT_PUBLIC_STRIPE_MONTHLY_PRICE_ID!;

      const res = await fetch('/api/create-checkout-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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

  return (
    <div className="flex min-h-screen flex-col items-center p-24">
      <div className="w-full max-w-lg text-center">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-4xl font-bold">Dashboard</h1>
          <button
            onClick={handleUpgrade}
            disabled={!user}
            className="px-4 py-2 font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
          >
            Upgrade to Pro
          </button>
        </div>
        <p className="mt-4 text-lg">
          Welcome, {user ? user.email : 'Guest'}. Upload your PDF file below to get started.
        </p>
        <div className="mt-8">
          <FileUpload />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const stripePromise = getStripe();
  return (
    <Elements stripe={stripePromise}>
      <DashboardContent />
    </Elements>
  )
}
