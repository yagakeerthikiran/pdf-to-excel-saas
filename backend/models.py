from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class FileStatus(enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing" 
    CONVERTED = "converted"
    FAILED = "failed"

class File(Base):
    __tablename__ = "files"
    
    id = Column(String, primary_key=True)  # UUID
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String, nullable=False)
    
    # S3 keys
    raw_s3_key = Column(String, nullable=False)
    converted_s3_key = Column(String, nullable=True)
    
    # Status tracking
    status = Column(Enum(FileStatus), default=FileStatus.UPLOADED)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="files")

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)  # Supabase UUID
    email = Column(String, unique=True, nullable=False)
    subscription_tier = Column(String, default="free")  # free, pro
    stripe_customer_id = Column(String, nullable=True)
    
    # Usage tracking
    daily_conversions = Column(Integer, default=0)
    monthly_conversions = Column(Integer, default=0)
    last_conversion_date = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    files = relationship("File", back_populates="user")

class ConversionJob(Base):
    __tablename__ = "conversion_jobs"
    
    id = Column(String, primary_key=True)  # UUID
    file_id = Column(String, ForeignKey("files.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Job tracking
    status = Column(String, default="pending")  # pending, processing, completed, failed
    worker_id = Column(String, nullable=True)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    file = relationship("File")
    user = relationship("User")