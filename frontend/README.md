# PDF to Excel Converter - Frontend

This is a [Next.js](https://nextjs.org) project built with TypeScript, TailwindCSS, and integrations for PostHog analytics and Sentry error tracking.

## Tech Stack

- **Framework**: Next.js 15.4.6 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS v4
- **Analytics**: PostHog
- **Error Tracking**: Sentry
- **Authentication**: Supabase (basic setup)

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm, yarn, pnpm, or bun

### Environment Setup

Create a `.env.local` file in the frontend directory with:

```env
# PostHog Analytics (optional for development)
NEXT_PUBLIC_POSTHOG_KEY=phc_your_posthog_key_here
NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com

# Sentry Error Tracking (optional for development)
NEXT_PUBLIC_SENTRY_DSN=your_sentry_dsn_here
```

**⚠️ Important Notes:**
- **PostHog Key Format**: Must start with `phc_` to be valid
- **Without Keys**: App works fine without these keys (analytics just won't track)
- **Never Commit**: Keep all secrets in environment files only

### Quick Test (No Setup Required)

The app works immediately without any environment variables:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and you should see the upload button.

## Windows Development Notes

### Clearing Cache
If you encounter build issues or need to clear the Next.js cache on Windows:

```powershell
cd C:\AI\GIT_Repos\pdf-to-excel-saas\frontend
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
```

### Execution Policy
If you encounter PowerShell execution policy issues:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
npm run dev
```

### Port Management
Next.js will automatically switch to port 3001 if 3000 is busy. Check the terminal output for the actual port being used.

## Troubleshooting

### Upload Button Not Visible
1. **Check Console**: Look for JavaScript errors in browser console
2. **Verify Build**: Run `npm run build` to check for TypeScript/build errors
3. **Clear Cache**: Use Windows cache clearing command above
4. **Check Port**: Ensure you're on the correct port (3000 or 3001)

### PostHog 401 Errors
1. **Check Key Format**: PostHog key must start with `phc_`
2. **Verify .env.local**: Ensure file is in `frontend/.env.local` 
3. **Restart Server**: After adding env vars, restart `npm run dev`
4. **Optional**: PostHog errors won't break the app functionality

### Environment Variables Not Loading
```bash
# Verify your .env.local file location
ls frontend/.env.local

# Check file contents (without showing secrets)
head -n 3 frontend/.env.local
```

## Features

### File Upload
- **Component**: `src/components/SimpleUploadCard.tsx` (no analytics) or `UploadCard.tsx` (with analytics)
- **API Route**: `src/app/api/upload/route.ts`
- **Features**: 
  - PDF file validation
  - 20MB size limit
  - Error handling
  - Success feedback

### Analytics Integration (Optional)
- **PostHog**: Initialized via `useEffect` in `src/app/providers.tsx`
- **Events Tracked**:
  - `upload_button_viewed`
  - `upload_button_clicked`
  - `file_selected`
  - `upload_started`
  - `upload_succeeded`
  - `upload_failed`

### Error Monitoring (Optional)
- **Sentry**: Configured for Next.js 15 with proper instrumentation hooks
- **Files**: 
  - `src/instrumentation.ts` (server hooks)
  - `src/instrumentation-client.ts` (client hooks)

## Manual Testing Steps

1. **Start Development Server**:
   ```bash
   npm run dev
   ```

2. **Upload Button Visibility**: 
   - Visit homepage
   - Verify upload card with blue button appears

3. **File Upload Flow**:
   - Click "Select PDF File" button
   - Choose a PDF file
   - Click "Upload PDF"
   - Verify success/error messages

4. **PostHog Events** (if configured):
   - Open browser dev tools
   - Check Network tab for PostHog requests
   - Verify no 401 errors in console

5. **Build Test**:
   ```bash
   npm run build
   ```
   - Verify build completes without Sentry or analytics errors

## Environment Variable Examples

```env
# Valid PostHog setup
NEXT_PUBLIC_POSTHOG_KEY=phc_abcd1234567890abcdef1234567890abcdef1234
NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com

# Valid Sentry setup  
NEXT_PUBLIC_SENTRY_DSN=https://abc123@def456.ingest.sentry.io/789012
```

## Build & Deploy

```bash
npm run build
npm start
```

The build process will:
- Compile TypeScript
- Generate optimized production bundle
- Initialize Sentry and PostHog configurations (if keys provided)

## Project Structure

```
src/
├── app/
│   ├── api/upload/          # API routes
│   ├── globals.css          # Global styles
│   ├── layout.tsx           # Root layout
│   ├── page.tsx             # Homepage
│   └── providers.tsx        # Client providers (PostHog)
├── components/
│   ├── SimpleUploadCard.tsx # Upload component (no analytics)
│   ├── UploadCard.tsx       # Upload component (with analytics)
│   └── PostHogProvider.tsx  # Legacy provider (deprecated)
├── instrumentation.ts       # Sentry server hooks
└── instrumentation-client.ts # Sentry client hooks
```

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [TailwindCSS v4 Docs](https://tailwindcss.com/docs)
- [PostHog Next.js Integration](https://posthog.com/docs/libraries/next-js)
- [Sentry Next.js SDK](https://docs.sentry.io/platforms/javascript/guides/nextjs/)