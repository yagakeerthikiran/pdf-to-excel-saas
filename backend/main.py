import os
import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
