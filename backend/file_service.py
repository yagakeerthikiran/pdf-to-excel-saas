from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from models import File, User, ConversionJob, FileStatus
from s3_service import s3_service
from datetime import datetime, timedelta
import uuid
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self, db: Session):
        self.db = db
        
    def create_upload_url(self, user_id: str, filename: str, content_type: str) -> Dict[str, Any]:
        """Create presigned upload URL and file record"""
        try:
            # Check user limits
            user = self.get_or_create_user(user_id)
            if not self.check_upload_limits(user):
                raise Exception("Upload limit exceeded")
            
            # Generate S3 upload URL
            s3_response = s3_service.generate_presigned_upload_url(
                user_id, filename, content_type
            )
            
            # Create file record
            file_record = File(
                id=s3_response['file_id'],
                user_id=user_id,
                original_filename=filename,
                file_size=0,  # Will be updated after upload
                content_type=content_type,
                raw_s3_key=s3_response['key'],
                status=FileStatus.UPLOADED
            )
            
            self.db.add(file_record)
            self.db.commit()
            
            return {
                'file_id': file_record.id,
                'upload_url': s3_response['upload_url'],
                'fields': s3_response['fields']
            }
            
        except Exception as e:
            logger.error(f"Error creating upload URL: {e}")
            self.db.rollback()
            raise
    
    def confirm_upload(self, file_id: str, user_id: str) -> Dict[str, Any]:
        """Confirm file upload and start conversion"""
        try:
            file_record = self.db.query(File).filter(
                and_(File.id == file_id, File.user_id == user_id)
            ).first()
            
            if not file_record:
                raise Exception("File not found")
            
            # Get file metadata from S3
            metadata = s3_service.get_file_metadata(file_record.raw_s3_key)
            if metadata:
                file_record.file_size = metadata.get('size', 0)
            
            # Create conversion job
            job = ConversionJob(
                id=str(uuid.uuid4()),
                file_id=file_id,
                user_id=user_id,
                status="pending"
            )
            
            file_record.status = FileStatus.PROCESSING
            
            self.db.add(job)
            self.db.commit()
            
            # Update user conversion count
            self.increment_user_conversions(user_id)
            
            return {
                'file_id': file_id,
                'job_id': job.id,
                'status': 'processing'
            }
            
        except Exception as e:
            logger.error(f"Error confirming upload: {e}")
            self.db.rollback()
            raise
    
    def get_user_files(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get user's files with download URLs"""
        try:
            files = self.db.query(File).filter(
                File.user_id == user_id
            ).order_by(desc(File.created_at)).offset(offset).limit(limit).all()
            
            result = []
            for file in files:
                file_data = {
                    'id': file.id,
                    'filename': file.original_filename,
                    'size': file.file_size,
                    'status': file.status.value,
                    'created_at': file.created_at.isoformat(),
                    'error_message': file.error_message
                }
                
                # Add download URLs if available
                if file.raw_s3_key:
                    file_data['pdf_download_url'] = s3_service.generate_presigned_download_url(
                        file.raw_s3_key
                    )
                
                if file.converted_s3_key and file.status == FileStatus.CONVERTED:
                    file_data['excel_download_url'] = s3_service.generate_presigned_download_url(
                        file.converted_s3_key
                    )
                
                result.append(file_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting user files: {e}")
            raise
    
    def update_conversion_status(self, job_id: str, status: str, error_message: str = None, converted_s3_key: str = None):
        """Update conversion job and file status"""
        try:
            job = self.db.query(ConversionJob).filter(ConversionJob.id == job_id).first()
            if not job:
                raise Exception("Job not found")
            
            job.status = status
            if error_message:
                job.error_message = error_message
            
            file_record = self.db.query(File).filter(File.id == job.file_id).first()
            if file_record:
                if status == "completed":
                    file_record.status = FileStatus.CONVERTED
                    file_record.converted_s3_key = converted_s3_key
                    file_record.processed_at = datetime.utcnow()
                    job.completed_at = datetime.utcnow()
                elif status == "failed":
                    file_record.status = FileStatus.FAILED
                    file_record.error_message = error_message
                    job.completed_at = datetime.utcnow()
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating conversion status: {e}")
            self.db.rollback()
            raise
    
    def get_or_create_user(self, user_id: str, email: str = None) -> User:
        """Get or create user record"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(
                id=user_id,
                email=email or f"user_{user_id}@temp.com",
                subscription_tier="free"
            )
            self.db.add(user)
            self.db.commit()
        return user
    
    def check_upload_limits(self, user: User) -> bool:
        """Check if user can upload based on their tier"""
        if user.subscription_tier == "pro":
            return True
        
        # Free tier limits: 5 conversions per day
        today = datetime.utcnow().date()
        if user.last_conversion_date and user.last_conversion_date.date() == today:
            return user.daily_conversions < 5
        
        return True
    
    def increment_user_conversions(self, user_id: str):
        """Increment user conversion count"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            today = datetime.utcnow().date()
            if user.last_conversion_date and user.last_conversion_date.date() == today:
                user.daily_conversions += 1
            else:
                user.daily_conversions = 1
            
            user.monthly_conversions += 1
            user.last_conversion_date = datetime.utcnow()
            self.db.commit()
    
    def get_pending_jobs(self, limit: int = 10) -> List[ConversionJob]:
        """Get pending conversion jobs for workers"""
        return self.db.query(ConversionJob).filter(
            ConversionJob.status == "pending"
        ).order_by(ConversionJob.created_at).limit(limit).all()
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        total_files = self.db.query(File).filter(File.user_id == user_id).count()
        converted_files = self.db.query(File).filter(
            and_(File.user_id == user_id, File.status == FileStatus.CONVERTED)
        ).count()
        
        return {
            'subscription_tier': user.subscription_tier,
            'daily_conversions': user.daily_conversions,
            'monthly_conversions': user.monthly_conversions,
            'total_files': total_files,
            'converted_files': converted_files,
            'conversion_rate': (converted_files / total_files * 100) if total_files > 0 else 0
        }