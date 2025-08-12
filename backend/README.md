# Backend

This directory contains the FastAPI application that handles the core business logic, including PDF conversion, user management, and payment processing. It is designed to be deployed as an AWS Lambda function.

## Key Technologies
- Python
- FastAPI
- `pdfplumber`, `camelot`, `openpyxl` (for PDF processing)
- AWS S3 (for file storage)
- Supabase (for database)
- Stripe (for webhooks)
- PostHog (for analytics)
- Sentry (for error tracking)

## Setup
Refer to the root `docs/SETUP.md` for instructions on setting up environment variables. To run the development server:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
