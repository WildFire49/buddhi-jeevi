import os
import uuid
from minio import Minio
from minio.error import S3Error
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MinioService:
    """Service for interacting with MinIO object storage"""
    
    def __init__(self):
        """Initialize MinIO client with environment variables"""
        self.endpoint = os.getenv("MINIO_ENDPOINT", "3.6.132.24")
        self.port = os.getenv("MINIO_PORT", "9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "SWMSC2SQP1ICJ0I84N81")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "bXwJ+wFwjpb9qP1S85bVsuXceO4oJtNK7+rZCS15")
        self.bucket_name = os.getenv("MINIO_BUCKET", "buddhi-images")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        # Parse the endpoint URL properly
        from urllib.parse import urlparse
        
        # Handle the endpoint URL format
        endpoint_url = self.endpoint
        parsed_url = urlparse(endpoint_url)
        
        # Extract hostname without scheme and path
        hostname = parsed_url.netloc if parsed_url.netloc else parsed_url.path
        
        # If there's still a scheme in the hostname, remove it
        if not hostname and parsed_url.scheme:
            hostname = parsed_url.scheme
            
        # Create MinIO client with proper endpoint format
        endpoint = f"{hostname}:{self.port}"
        logger.info(f"Connecting to MinIO at {endpoint}")
        
        self.client = Minio(
            endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.info(f"Bucket already exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise
    
    def upload_file(self, file_data: bytes, file_name: str, content_type: str) -> str:
        """
        Upload a file to MinIO
        
        Args:
            file_data: The file data as bytes
            file_name: Original file name (used only for extension)
            content_type: MIME type of the file
            
        Returns:
            str: The unique object ID
        """
        try:
            # Generate a unique ID for the file
            object_id = str(uuid.uuid4())
            
            # Extract file extension from original filename
            _, file_extension = os.path.splitext(file_name)
            
            # Create the object name with the unique ID and original extension
            object_name = f"{object_id}{file_extension}"
            
            # Import BytesIO to create a file-like object from bytes
            from io import BytesIO
            
            # Create a file-like object from the bytes data
            file_data_io = BytesIO(file_data)
            
            # Upload the file using the file-like object
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_data_io,
                length=len(file_data),
                content_type=content_type
            )
            
            logger.info(f"Uploaded file with ID {object_id}")
            return object_id
            
        except S3Error as e:
            print(f"Error uploading file {file_name}: {e}")
            logger.error(f"Error uploading file {file_name}: {e}")
            return e
    
    def get_file_url(self, object_id: str) -> Optional[str]:
        """
        Get a URL for accessing the file
        
        Args:
            object_id: The unique object ID
            
        Returns:
            Optional[str]: URL to access the file or None if not found
        """
        try:
            # List objects with the prefix to find the full object name with extension
            objects = self.client.list_objects(self.bucket_name, prefix=object_id, recursive=True)
            
            for obj in objects:
                # Generate a presigned URL for the object
                # Use timedelta for expires parameter
                from datetime import timedelta
                
                url = self.client.presigned_get_object(
                    bucket_name=self.bucket_name,
                    object_name=obj.object_name,
                    expires=timedelta(days=7)  # URL valid for 7 days
                )
                return url
                
            return None
            
        except S3Error as e:
            logger.error(f"Error getting URL for object {object_id}: {e}")
            return None
