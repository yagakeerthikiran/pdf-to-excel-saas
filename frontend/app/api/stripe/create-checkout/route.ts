export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'

let stripeSingleton: import('stripe').Stripe | null = null
function getStripe() {
  if (!stripeSingleton) {
    const key = process.env.STRIPE_SECRET_KEY
    if (!key) throw new Error('STRIPE_SECRET_KEY is not set')
    // require() to avoid ESM import at build time
    const Stripe = require('stripe').default as typeof import('stripe').default
    stripeSingleton = new Stripe(key, { apiVersion: '2023-10-16' })
  }
  return stripeSingleton
}

export async function POST(req: NextRequest) {
  const { priceId, quantity = 1, metadata } = await req.json()

  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL ?? 'http://localhost:3000'
  const stripe = getStripe()

  const session = await stripe.checkout.sessions.create({
    mode: 'payment',
    line_items: [{ price: priceId, quantity }],
    success_url: `${baseUrl}/payment/success?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${baseUrl}/payment/cancel`,
    metadata,
  })

  return NextResponse.json({ id: session.id, url: session.url })
}
