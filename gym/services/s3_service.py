import boto3
import os
from django.conf import settings
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self):
        # Debug: Check if credentials are loaded
        logger.info(f"AWS_ACCESS_KEY_ID: {settings.AWS_ACCESS_KEY_ID[:5] if settings.AWS_ACCESS_KEY_ID else 'None'}...")
        logger.info(f"AWS_STORAGE_BUCKET_NAME: {settings.AWS_STORAGE_BUCKET_NAME}")
        logger.info(f"AWS_S3_ENDPOINT_URL: {getattr(settings, 'AWS_S3_ENDPOINT_URL', 'Not set')}")
        
        client_config = {
            'aws_access_key_id': settings.AWS_ACCESS_KEY_ID,
            'aws_secret_access_key': settings.AWS_SECRET_ACCESS_KEY,
            'region_name': settings.AWS_S3_REGION_NAME
        }
        
        # Add endpoint URL for MinIO or custom S3-compatible services
        if hasattr(settings, 'AWS_S3_ENDPOINT_URL') and settings.AWS_S3_ENDPOINT_URL:
            client_config['endpoint_url'] = settings.AWS_S3_ENDPOINT_URL
        
        self.s3_client = boto3.client('s3', **client_config)
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    def upload_file(self, file_obj, key: str, content_type: str = None) -> Optional[str]:
        """Upload file to S3 bucket"""
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                key,
                ExtraArgs=extra_args
            )
            return self.get_file_url(key)
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {e}")
            return None

    def delete_file(self, key: str) -> bool:
        """Delete file from S3 bucket"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False

    def get_file_url(self, key: str) -> str:
        """Get file URL"""
        if settings.AWS_S3_CUSTOM_DOMAIN:
            return f"{settings.AWS_S3_CUSTOM_DOMAIN}/{self.bucket_name}/{key}"
        
        # Handle MinIO or custom endpoint
        if hasattr(settings, 'AWS_S3_ENDPOINT_URL') and settings.AWS_S3_ENDPOINT_URL:
            return f"{settings.AWS_S3_ENDPOINT_URL}/{self.bucket_name}/{key}"
        
        return f"https://{self.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{key}"

    def generate_presigned_url(self, key: str, expiration: int = 3600) -> Optional[str]:
        """Generate presigned URL for file access"""
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None

    def file_exists(self, key: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False