import boto3
import time
import structlog
from typing import List, Dict, Any

logger = structlog.get_logger(__name__)

Element = Dict[str, Any]

def parse_textract_response(response: dict) -> List[Element]:
    """
    Parses the raw JSON response from AWS Textract and transforms it into
    our simple List[Element] format.
    """
    elements = []

    # Textract returns a list of 'Block' objects. We are interested in 'WORD' types.
    # We use WORD because it gives us the most granular bounding box information.
    for block in response.get("Blocks", []):
        if block["BlockType"] == "WORD":
            text = block.get("Text", "")
            geom = block.get("Geometry", {})
            bbox = geom.get("BoundingBox", {})

            # Textract's bounding box is proportional (0.0-1.0). We don't need to
            # convert it for now, but we would if we needed absolute pixel values.
            # For our layout engine, we just need the coordinates.
            # Note: Textract uses 'Left' and 'Top', not x0, y0. We can adapt.
            # For now, let's just extract the raw data. The layout engine will need to be
            # made aware of this different format.
            # Let's stick to the x0, top, x1, bottom format for consistency.
            # We'll need page dimensions to convert. Let's assume a page width/height
            # for now, or pass it in. This is getting complex.

            # Let's simplify: for now, we just return the text and the geometry.
            # The conversion service will need to handle this.
            # This is not ideal. Let's make a decision: The OCR service
            # should conform to the Element spec. But it can't without page dimensions.

            # New decision: The OCR service will return a list of Textract blocks,
            # and the conversion service will be responsible for parsing them.
            # This is a better separation of concerns.

            # Let's reverse that decision. The OCR service SHOULD do the parsing.
            # It's the "ocr_service". But it needs page dimensions.
            # The calling function in conversion_service will have the page dimensions.
            # So, we should pass them in.

            # Let's stick to the original plan. This service does it all.
            # The calling function will just get the simple List[Element].
            # But the Textract API doesn't give us the page dimensions easily.

            # OK, final, simplest, most robust decision:
            # This service gets the blocks. The main conversion service, which has
            # access to the pdfplumber page object (and thus its dimensions), will
            # be responsible for the final conversion to our Element format.
            # This is the best separation of concerns.
            pass # We will implement the full logic in the next step.

    # For now, this function will be a placeholder.
    # The real implementation will be complex.
    logger.info("Parsing Textract response... (placeholder)")
    return []


def get_textract_results(job_id: str) -> dict:
    """
    Paginates through the results of a completed Textract job.
    """
    textract = boto3.client("textract")
    all_blocks = []

    response = textract.get_document_analysis(JobId=job_id)
    all_blocks.extend(response.get("Blocks", []))

    next_token = response.get("NextToken")
    while next_token:
        response = textract.get_document_analysis(JobId=job_id, NextToken=next_token)
        all_blocks.extend(response.get("Blocks", []))
        next_token = response.get("NextToken")

    return {"Blocks": all_blocks}


def extract_data_with_textract(bucket_name: str, object_key: str) -> dict:
    """
    Starts a Textract analysis job for a PDF in S3, waits for it to complete,
    and returns the full result.
    """
    textract = boto3.client("textract")
    logger.info("Starting Textract analysis job", bucket=bucket_name, key=object_key)

    try:
        response = textract.start_document_analysis(
            DocumentLocation={"S3Object": {"Bucket": bucket_name, "Name": object_key}},
            FeatureTypes=["TABLES", "FORMS"]
        )
        job_id = response["JobId"]
        logger.info("Textract job started", job_id=job_id)

        # Poll for completion
        while True:
            job_status_response = textract.get_document_analysis(JobId=job_id)
            status = job_status_response["JobStatus"]
            logger.info(f"Polling Textract job status: {status}", job_id=job_id)

            if status == "SUCCEEDED":
                break
            elif status == "FAILED":
                logger.error("Textract job failed", job_id=job_id, response=job_status_response)
                raise Exception(f"Textract job {job_id} failed.")

            time.sleep(5) # Wait 5 seconds before polling again

        logger.info("Textract job succeeded. Fetching results...", job_id=job_id)
        full_results = get_textract_results(job_id)

        return full_results

    except Exception as e:
        logger.error("An error occurred with AWS Textract", error=str(e), exc_info=True)
        raise
