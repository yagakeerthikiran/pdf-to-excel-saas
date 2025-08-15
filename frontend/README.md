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
NEXT_PUBLIC_POSTHOG_KEY=phc_...
NEXT_PUBLIC_POSTHOG_HOST=https://us.i.posthog.com
NEXT_PUBLIC_SENTRY_DSN=...
```

⚠️ **Important**: Keep all secrets in environment files only. Never commit API keys to the repository.

### Development Server

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

**Note**: If port 3000 is busy, Next.js will automatically switch to port 3001.

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

## Features

### File Upload
- **Component**: `src/components/UploadCard.tsx`
- **API Route**: `src/app/api/upload/route.ts`
- **Features**: 
  - PDF file validation
  - 20MB size limit
  - PostHog event tracking
  - Error handling

### Analytics Integration
- **PostHog**: Initialized via `useEffect` in `src/app/providers.tsx`
- **Events Tracked**:
  - `upload_button_viewed`
  - `upload_button_clicked`
  - `file_selected`
  - `upload_started`
  - `upload_succeeded`
  - `upload_failed`

### Error Monitoring
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
   - Verify upload card is visible and interactive

3. **File Upload Flow**:
   - Click "Select PDF File" button
   - Choose a PDF file
   - Click "Upload PDF"
   - Verify success/error messages

4. **PostHog Events**:
   - Open browser dev tools
   - Check Network tab for PostHog requests
   - Verify no 401 errors in console

5. **Build Test**:
   ```bash
   npm run build
   ```
   - Verify build completes without Sentry or analytics errors

## Build & Deploy

```bash
npm run build
npm start
```

The build process will:
- Compile TypeScript
- Generate optimized production bundle
- Initialize Sentry and PostHog configurations

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
│   ├── UploadCard.tsx       # Main upload component
│   └── PostHogProvider.tsx  # Legacy provider (deprecated)
├── instrumentation.ts       # Sentry server hooks
└── instrumentation-client.ts # Sentry client hooks
```

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [TailwindCSS v4 Docs](https://tailwindcss.com/docs)
- [PostHog Next.js Integration](https://posthog.com/docs/libraries/next-js)
- [Sentry Next.js SDK](https://docs.sentry.io/platforms/javascript/guides/nextjs/)