import asyncio
import logging
import os
import boto3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import ConversionJob, File, FileStatus
from file_service import FileService
from s3_service import s3_service
from conversion_service import ConversionService
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversionWorker:
    def __init__(self):
        # Database setup
        database_url = os.getenv('DATABASE_URL')
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Services
        self.conversion_service = ConversionService()
        
        # Worker configuration
        self.worker_id = os.getenv('WORKER_ID', 'worker-1')
        self.poll_interval = int(os.getenv('POLL_INTERVAL', '10'))  # seconds
        self.max_concurrent_jobs = int(os.getenv('MAX_CONCURRENT_JOBS', '5'))
        
        logger.info(f"Worker {self.worker_id} initialized")

    async def start(self):
        """Start the worker to process conversion jobs"""
        logger.info(f"Worker {self.worker_id} starting...")
        
        while True:
            try:
                await self.process_pending_jobs()
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(self.poll_interval)

    async def process_pending_jobs(self):
        """Process pending conversion jobs"""
        db = self.SessionLocal()
        try:
            file_service = FileService(db)
            
            # Get pending jobs
            pending_jobs = file_service.get_pending_jobs(limit=self.max_concurrent_jobs)
            
            if not pending_jobs:
                return
            
            logger.info(f"Found {len(pending_jobs)} pending jobs")
            
            # Process jobs concurrently
            tasks = []
            for job in pending_jobs:
                task = asyncio.create_task(self.process_job(job))
                tasks.append(task)
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
        finally:
            db.close()

    async def process_job(self, job: ConversionJob):
        """Process a single conversion job"""
        db = self.SessionLocal()
        try:
            file_service = FileService(db)
            
            logger.info(f"Processing job {job.id} for file {job.file_id}")
            
            # Update job status to processing
            job.status = "processing"
            job.worker_id = self.worker_id
            job.attempts += 1
            db.commit()
            
            # Get file record
            file_record = db.query(File).filter(File.id == job.file_id).first()
            if not file_record:
                raise Exception("File record not found")
            
            # Download PDF from S3
            logger.info(f"Downloading PDF from S3: {file_record.raw_s3_key}")
            pdf_data = await self.download_from_s3(file_record.raw_s3_key)
            
            # Convert PDF to Excel
            logger.info(f"Converting PDF to Excel")
            excel_data = await self.convert_pdf_to_excel(pdf_data, file_record.original_filename)
            
            # Upload Excel to S3
            logger.info(f"Uploading Excel to S3")
            excel_s3_key = s3_service.upload_converted_file(
                job.user_id, 
                job.file_id, 
                excel_data, 
                file_record.original_filename
            )
            
            # Update job and file status
            file_service.update_conversion_status(
                job.id, 
                "completed", 
                converted_s3_key=excel_s3_key
            )
            
            logger.info(f"Job {job.id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job {job.id} failed: {e}")
            
            # Update job status to failed
            try:
                file_service = FileService(db)
                file_service.update_conversion_status(
                    job.id, 
                    "failed", 
                    error_message=str(e)
                )
            except Exception as update_error:
                logger.error(f"Failed to update job status: {update_error}")
        
        finally:
            db.close()

    async def download_from_s3(self, s3_key: str) -> bytes:
        """Download file from S3"""
        try:
            response = s3_service.s3_client.get_object(
                Bucket=s3_service.bucket_name, 
                Key=s3_key
            )
            return response['Body'].read()
        except Exception as e:
            raise Exception(f"Failed to download from S3: {e}")

    async def convert_pdf_to_excel(self, pdf_data: bytes, filename: str) -> bytes:
        """Convert PDF to Excel using the conversion service"""
        try:
            # Save PDF to temporary file
            temp_pdf_path = f"/tmp/{filename}"
            with open(temp_pdf_path, 'wb') as f:
                f.write(pdf_data)
            
            # Convert using existing conversion service
            excel_path = await asyncio.to_thread(
                self.conversion_service.convert_pdf_to_excel, 
                temp_pdf_path
            )
            
            # Read Excel data
            with open(excel_path, 'rb') as f:
                excel_data = f.read()
            
            # Cleanup temporary files
            os.remove(temp_pdf_path)
            if os.path.exists(excel_path):
                os.remove(excel_path)
            
            return excel_data
            
        except Exception as e:
            raise Exception(f"PDF conversion failed: {e}")

async def main():
    """Main entry point for the worker"""
    worker = ConversionWorker()
    await worker.start()

if __name__ == "__main__":
    asyncio.run(main())