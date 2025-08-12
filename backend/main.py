import os
import boto3
import stripe
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv
import backend.user_service as user_service

# Load environment variables from .env file
load_dotenv()

# Configure Stripe API key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

app = FastAPI(
    title="PDF to Excel API",
    description="The backend service for the PDF to Excel conversion application.",
    version="0.1.0"
)


class ConversionResponse(BaseModel):
    success: bool
    message: str
    download_url: str | None = None


class GenerateUploadUrlRequest(BaseModel):
    filename: str
    content_type: str


class GenerateUploadUrlResponse(BaseModel):
    url: str
    fields: dict


class ConversionRequest(BaseModel):
    fileKey: str


class CheckoutSessionRequest(BaseModel):
    price_id: str
    user_id: str # This is a temporary solution for passing the user ID.


class CheckoutSessionResponse(BaseModel):
    session_id: str

@app.get("/")
def read_root():
    """
    Root endpoint providing a welcome message.
    """
    return {"message": "Welcome to the PDF to Excel API"}


@app.get("/health", status_code=200)
def health_check():
    """
    Health check endpoint for uptime monitoring.
    """
    return {"status": "ok"}


@app.post("/generate-upload-url", response_model=GenerateUploadUrlResponse)
def generate_upload_url(req: GenerateUploadUrlRequest):
    """
    Generates a pre-signed URL for uploading a file to S3.
    """
    s3_client = boto3.client('s3', region_name=os.getenv("AWS_REGION"))
    bucket_name = os.getenv("S3_BUCKET_NAME")

    # The key is the path to the file in the S3 bucket.
    # We can add a user ID or a UUID here to make it unique.
    # For now, we'll just use the filename.
    object_key = f"uploads/{req.filename}"

    try:
        response = s3_client.generate_presigned_post(
            Bucket=bucket_name,
            Key=object_key,
            Fields={"Content-Type": req.content_type},
            Conditions=[{"Content-Type": req.content_type}],
            ExpiresIn=3600  # URL expires in 1 hour
        )
    except ClientError as e:
        print(f"Error generating pre-signed URL: {e}")
        raise HTTPException(status_code=500, detail="Could not generate upload URL.")

    return response


@app.post("/create-checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(req: CheckoutSessionRequest):
    """
    Creates a Stripe Checkout session for a given price ID.
    """
    try:
        # For now, we get the base URL from an env var.
        # This will be the URL of our deployed frontend.
        base_url = os.getenv("BASE_URL", "http://localhost:3000")

        checkout_session = stripe.checkout.Session.create(
            client_reference_id=req.user_id,
            payment_method_types=['card'],
            line_items=[
                {
                    'price': req.price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=f'{base_url}/dashboard?success=true&session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{base_url}/dashboard?canceled=true',
        )
        return {"session_id": checkout_session.id}
    except Exception as e:
        print(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stripe-webhook")
async def stripe_webhook(request: Request):
    """
    Handles incoming webhooks from Stripe.
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig_header, secret=endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail=str(e))
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail=str(e))

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        client_reference_id = session.get('client_reference_id')
        if client_reference_id:
            print(f"Checkout session completed for user: {client_reference_id}. Updating status to 'pro'.")
            user_service.update_subscription_status(client_reference_id, 'pro')
        else:
            print("Warning: checkout.session.completed event received without a client_reference_id.")
    elif event['type'] == 'customer.subscription.deleted':
        session = event['data']['object']
        # This is a bit more complex, we'd need to get the user_id from the customer_id
        print(f"Subscription deleted for customer: {session.get('customer')}. Setting status to 'free'.")
        # user_service.update_subscription_status_by_customer(session.get('customer'), 'free')
    else:
        print(f"Unhandled event type {event['type']}")

    return {"status": "success"}


@app.post("/convert", response_model=ConversionResponse)
async def convert_pdf(req: ConversionRequest):
    """
    Mock endpoint for PDF to Excel conversion.
    This will be replaced with actual conversion logic.
    It receives the S3 key of the uploaded file.
    """
    print(f"Received request to convert file with key: {req.fileKey}")

    # Placeholder for actual conversion logic
    # 1. Download file from S3 using fileKey
    # 2. Process with pdfplumber/camelot
    # 3. Upload resulting Excel to S3
    # 4. Generate a pre-signed URL for the Excel file

    return {
        "success": True,
        "message": f"File '{req.fileKey}' converted successfully (mock response).",
        "download_url": "https://example.com/mock-download-url.xlsx"
    }
