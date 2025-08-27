export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

import PricingPlans from '@/components/PricingPlans'

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <PricingPlans />
    </div>
  )
}

