import boto3
import uuid
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import os
import logging

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
        self.raw_folder = 'raw/'
        self.converted_folder = 'converted/'
        
    def generate_presigned_upload_url(self, user_id: str, filename: str, content_type: str) -> dict:
        """Generate presigned URL for direct frontend upload to S3"""
        try:
            file_id = str(uuid.uuid4())
            key = f"{self.raw_folder}{user_id}/{file_id}_{filename}"
            
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=key,
                Fields={'Content-Type': content_type},
                Conditions=[
                    {'Content-Type': content_type},
                    ['content-length-range', 1, 20971520]  # 1 byte to 20MB
                ],
                ExpiresIn=3600  # 1 hour
            )
            
            return {
                'upload_url': response['url'],
                'fields': response['fields'],
                'file_id': file_id,
                'key': key
            }
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise Exception("Failed to generate upload URL")
    
    def generate_presigned_download_url(self, key: str, expiration: int = 3600) -> str:
        """Generate presigned URL for file download"""
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            logger.error(f"Error generating download URL: {e}")
            raise Exception("Failed to generate download URL")
    
    def upload_converted_file(self, user_id: str, file_id: str, excel_data: bytes, original_filename: str) -> str:
        """Upload converted Excel file to S3"""
        try:
            excel_filename = f"{original_filename.replace('.pdf', '')}.xlsx"
            key = f"{self.converted_folder}{user_id}/{file_id}_{excel_filename}"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=excel_data,
                ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            return key
        except ClientError as e:
            logger.error(f"Error uploading converted file: {e}")
            raise Exception("Failed to upload converted file")
    
    def check_file_exists(self, key: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False
    
    def delete_file(self, key: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def get_file_metadata(self, key: str) -> dict:
        """Get file metadata from S3"""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response.get('ContentType'),
                'etag': response['ETag']
            }
        except ClientError as e:
            logger.error(f"Error getting file metadata: {e}")
            return {}

# Initialize service
s3_service = S3Service()