// Client hooks for Next.js 15 Sentry integration
import * as Sentry from '@sentry/nextjs'

// Required by Sentry for navigation instrumentation (Next 15)
export const onRouterTransitionStart = Sentry.captureRouterTransitionStart

// Optional: mark request component tree errors from nested RSC
export const onRequestError = Sentry.captureRequestError