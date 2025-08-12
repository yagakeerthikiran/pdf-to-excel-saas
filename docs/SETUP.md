# Project Setup and Credentials

This document provides instructions on how to set up your environment variables to run the application. Create a `.env` file in the `backend/` directory and a `.env.local` file in the `frontend/` directory and populate them with the values below.

---

## 1. AWS Credentials

These are required for the Serverless Framework to deploy the backend infrastructure and for the backend to access services like S3.

**Location:** `backend/.env`

```
# Your AWS access key ID
AWS_ACCESS_KEY_ID=
# Your AWS secret access key
AWS_SECRET_ACCESS_KEY=
# The AWS region you want to deploy to (e.g., us-east-1)
AWS_REGION=
# The name of the S3 bucket for temporary file storage
S3_BUCKET_NAME=
```
**How to get them:**
1.  Log in to your AWS Console.
2.  Go to the IAM service.
3.  Create a new user with programmatic access.
4.  Attach the necessary permissions (e.g., AdministratorAccess for initial setup, can be scoped down later).
5.  Save the generated Access Key ID and Secret Access Key.
6.  For the S3 bucket, go to the S3 service and create a new bucket. Ensure the name is globally unique.
7.  **IMPORTANT**: You must also configure CORS on your S3 bucket to allow uploads from the web application. Go to your bucket in the S3 console, click on the "Permissions" tab, and scroll down to "Cross-origin resource sharing (CORS)". Click "Edit" and paste the following JSON. Replace `http://localhost:3000` with your actual frontend domain when you go to production.

```json
[
    {
        "AllowedHeaders": [
            "*"
        ],
        "AllowedMethods": [
            "POST",
            "PUT"
        ],
        "AllowedOrigins": [
            "http://localhost:3000"
        ],
        "ExposeHeaders": []
    }
]
```

---

## 2. Supabase Configuration

Supabase is used for the database and user authentication.

### Frontend Supabase Configuration
**Location:** `frontend/.env.local`
```
# The URL of your Supabase project
NEXT_PUBLIC_SUPABASE_URL=
# The public anon key for your Supabase project (for use in the browser)
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```
*Note: The `NEXT_PUBLIC_` prefix is important for Next.js to expose these variables to the browser.*

### Backend Supabase Configuration
**Location:** `backend/.env`
```
# The URL of your Supabase project
SUPABASE_URL=
# The service_role key for your Supabase project (for backend use ONLY)
SUPABASE_SERVICE_KEY=
```

**How to get them:**
1.  Go to [Supabase](https://supabase.com/).
2.  Create a new project.
3.  Navigate to Project Settings > API.
4.  You will find the Project URL, the `anon` `public` key (for the frontend), and the `service_role` `secret` key (for the backend).
5.  **NEVER expose the `service_role` key in your frontend code.**

---

## 3. Stripe Configuration

Stripe is used for processing subscriptions.

**Location:** `backend/.env` AND `frontend/.env.local`

```
# Your Stripe public key (for the frontend)
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=

# Your Stripe secret key (for the backend)
STRIPE_SECRET_KEY=

# The ID of your "Monthly" subscription product in Stripe
STRIPE_MONTHLY_PRICE_ID=

# The ID of your "Yearly" subscription product in Stripe
STRIPE_YEARLY_PRICE_ID=

# The secret for your Stripe webhook endpoint (generate a random string)
STRIPE_WEBHOOK_SECRET=
```

**How to get them:**
1.  Log in to your Stripe Dashboard.
2.  Make sure you are in **Test mode**.
3.  Go to Developers > API keys to find your Publishable key (`pk_test_...`) and Secret key (`sk_test_...`).
4.  Go to Products to create your Monthly and Yearly subscription products and get their Price IDs.
5.  Go to Developers > Webhooks. When you create the endpoint, Stripe will provide you with a webhook signing secret.

---

## 4. Monitoring Services

These are for error tracking and product analytics.

### Sentry

**Location:** `backend/.env` AND `frontend/.env.local`
```
# The DSN for your Sentry project
NEXT_PUBLIC_SENTRY_DSN=
```

### PostHog

**Location:** `frontend/.env.local`
```
# Your PostHog project API key
NEXT_PUBLIC_POSTHOG_KEY=
# The URL of your PostHog instance
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com
```

**How to get them:**
1.  Sign up for accounts at [Sentry.io](https://sentry.io) and [PostHog](https://posthog.com).
2.  Create a new project for each service.
3.  In the project settings, you will find the DSN (for Sentry) and the API Key (for PostHog). Copy these values.
