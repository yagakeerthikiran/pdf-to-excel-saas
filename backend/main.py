import os
import boto3
import stripe
import sentry_sdk
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
import backend.user_service as user_service
import structlog
from backend.logging_config import setup_logging
from backend.conversion_service import convert_pdf_to_excel
from backend.security import enforce_usage_limits, get_current_user_id_from_header

# Load environment variables from .env file
load_dotenv()

# Set up logging
setup_logging()
logger = structlog.get_logger(__name__)

# Configure Stripe API key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Configure Sentry
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        # Enable performance monitoring
        traces_sample_rate=1.0,
    )

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
def generate_upload_url(req: GenerateUploadUrlRequest, _: dict = Depends(enforce_usage_limits)):
    """
    Generates a pre-signed URL for uploading a file to S3.
    This endpoint is protected by usage limit enforcement.
    """
    s3_client = boto3.client('s3', region_name=os.getenv("AWS_REGION"))
    bucket_name = os.getenv("S3_BUCKET_NAME")
    object_key = f"uploads/{req.filename}"

    try:
        logger.info("Generating pre-signed URL", bucket=bucket_name, key=object_key)
        # Enforce a 20MB file size limit
        max_file_size_bytes = 20 * 1024 * 1024

        conditions = [
            {"Content-Type": req.content_type},
            ["content-length-range", 0, max_file_size_bytes]
        ]

        fields = {"Content-Type": req.content_type}

        response = s3_client.generate_presigned_post(
            Bucket=bucket_name,
            Key=object_key,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=3600
        )
    except ClientError as e:
        logger.error("Error generating pre-signed URL", error=str(e))
        raise HTTPException(status_code=500, detail="Could not generate upload URL.")

    return response


@app.post("/create-checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(req: CheckoutSessionRequest):
    """
    Creates a Stripe Checkout session for a given price ID.
    """
    try:
        base_url = os.getenv("BASE_URL", "http://localhost:3000")
        checkout_session = stripe.checkout.Session.create(
            client_reference_id=req.user_id,
            payment_method_types=['card'],
            line_items=[{'price': req.price_id, 'quantity': 1}],
            mode='subscription',
            success_url=f'{base_url}/dashboard?success=true&session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{base_url}/dashboard?canceled=true',
        )
        logger.info("Created Stripe Checkout session", session_id=checkout_session.id)
        return {"session_id": checkout_session.id}
    except Exception as e:
        logger.error("Error creating checkout session", error=str(e))
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
        event = stripe.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=endpoint_secret)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    event_type = event['type']
    logger.info("Received Stripe webhook", event_type=event_type)
    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        client_reference_id = session.get('client_reference_id')
        if client_reference_id:
            logger.info("Checkout session completed, updating user status.", user_id=client_reference_id, new_status='pro')
            user_service.update_subscription_status(client_reference_id, 'pro')
        else:
            logger.warn("checkout.session.completed event received without client_reference_id.")
    elif event_type == 'customer.subscription.deleted':
        session = event['data']['object']
        customer_id = session.get('customer')
        logger.info("Subscription deleted, updating user status.", customer_id=customer_id, new_status='free')
    else:
        logger.warn("Unhandled Stripe event type", event_type=event_type)
    return {"status": "success"}


@app.get("/usage")
def get_user_usage(user_id: str = Depends(get_current_user_id_from_header)):
    """
    Gets the current usage stats for the authenticated user.
    """
    usage_data = user_service.get_usage(user_id)
    if not usage_data:
        raise HTTPException(status_code=404, detail="User profile not found.")
    return usage_data


@app.post("/handle-sentry-alert")
async def handle_sentry_alert(request: Request):
    """
    Handles incoming webhooks from Sentry for new issues.
    """
    payload = await request.json()
    logger.info("Received Sentry alert webhook", payload=payload)
    return {"status": "received"}


@app.post("/convert", response_model=ConversionResponse)
async def convert_pdf(req: ConversionRequest, user_id: str = Depends(get_current_user_id_from_header)):
    """
    Downloads a PDF from S3, converts it to Excel, and returns a download URL.
    Also increments the user's conversion count.
    """
    logger.info("Received request to convert file", file_key=req.fileKey, user_id=user_id)

    s3_client = boto3.client('s3', region_name=os.getenv("AWS_REGION"))
    bucket_name = os.getenv("S3_BUCKET_NAME")

    base_filename = os.path.splitext(os.path.basename(req.fileKey))[0]

    local_pdf_path = f"/tmp/{base_filename}.pdf"
    local_excel_path = f"/tmp/{base_filename}.xlsx"
    result_s3_key = f"results/{base_filename}.xlsx"

    try:
        logger.info("Downloading source PDF from S3", bucket=bucket_name, key=req.fileKey)
        s3_client.download_file(bucket_name, req.fileKey, local_pdf_path)

        convert_pdf_to_excel(local_pdf_path, local_excel_path, bucket_name, req.fileKey)

        logger.info("Uploading result Excel to S3", bucket=bucket_name, key=result_s3_key)
        s3_client.upload_file(local_excel_path, bucket_name, result_s3_key)

        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': result_s3_key},
            ExpiresIn=3600
        )

        user_service.increment_conversion_count(user_id)
        logger.info("Successfully incremented conversion count for user", user_id=user_id)

        return {
            "success": True,
            "message": "File converted successfully.",
            "download_url": download_url
        }

    except Exception as e:
        logger.error("An error occurred during the conversion process", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred during conversion.")
    finally:
        if os.path.exists(local_pdf_path):
            os.remove(local_pdf_path)
        if os.path.exists(local_excel_path):
            os.remove(local_excel_path)
