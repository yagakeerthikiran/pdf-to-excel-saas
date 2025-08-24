import { loadStripe } from '@stripe/stripe-js'

export const stripe = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!)

export const STRIPE_PRICE_IDS = {
  PRO: process.env.NEXT_PUBLIC_STRIPE_PRO_PRICE_ID!,
}

export const PLANS = {
  FREE: {
    name: 'Free',
    price: 0,
    conversions: 5,
    features: [
      '5 PDF conversions per month',
      'Basic table detection',
      'Standard accuracy',
      'Email support'
    ]
  },
  PRO: {
    name: 'Professional',
    price: 29,
    conversions: 500,
    priceId: STRIPE_PRICE_IDS.PRO,
    features: [
      '500 PDF conversions per month',
      'Advanced AI table detection',
      'Premium accuracy with OCR',
      'Priority email support',
      'Bulk processing',
      'API access'
    ]
  }
}
