'use client'

import * as Sentry from '@sentry/nextjs'
import { useEffect } from 'react'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    // This is where we report the error to Sentry
    Sentry.captureException(error)
  }, [error])

  return (
    <html>
      <body>
        <h2>Something went wrong!</h2>
        <p>An unexpected error occurred. Our team has been notified.</p>
        <button onClick={() => reset()}>Try again</button>
      </body>
    </html>
  )
}
