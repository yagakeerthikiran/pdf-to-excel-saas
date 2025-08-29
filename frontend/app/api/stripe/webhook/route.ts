export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

import { NextRequest, NextResponse } from 'next/server'

let stripeSingleton: import('stripe').Stripe | null = null
function getStripe() {
  if (!stripeSingleton) {
    const key = process.env.STRIPE_SECRET_KEY
    if (!key) throw new Error('STRIPE_SECRET_KEY not set')
    // require to avoid ESM at build-time
    const Stripe = require('stripe').default as typeof import('stripe').default
    stripeSingleton = new Stripe(key, { apiVersion: '2023-10-16' })
  }
  return stripeSingleton
}

export async function POST(req: NextRequest) {
  const sig = req.headers.get('stripe-signature')
  const raw = await req.text()
  try {
    let event: any

    if (process.env.NODE_ENV === 'production') {
      const secret = process.env.STRIPE_WEBHOOK_SECRET
      if (!secret || !sig) {
        return NextResponse.json({ error: 'Missing signature/secret' }, { status: 400 })
      }
      event = getStripe().webhooks.constructEvent(raw, sig, secret)
    } else {
      // Dev fallback: accept unverified JSON (so you can test from Dashboard without CLI)
      event = JSON.parse(raw || '{}')
    }

    switch (event.type) {
      case 'checkout.session.completed':
        // TODO: mark subscription active, etc.
        break
      default:
        // no-op
        break
    }

    return NextResponse.json({ received: true })
  } catch (err: any) {
    console.error('Webhook error:', err?.message || err)
    return NextResponse.json({ error: 'Webhook handler error' }, { status: 400 })
  }
}
