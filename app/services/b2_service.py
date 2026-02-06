"""
Backblaze B2 S3-compatible presigned URL helpers.
"""

from typing import Dict
import boto3
from botocore.config import Config
from app.core.config import settings


def get_b2_client():
    """Create an S3 client for Backblaze B2 using v4 signatures."""
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"})
    )


def generate_presigned_put_url(file_key: str, content_type: str, expires_in: int = 3600) -> Dict[str, str]:
    """Generate a presigned PUT URL for uploads."""
    client = get_b2_client()
    upload_url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.BUCKET_NAME,
            "Key": file_key,
            "ContentType": content_type
        },
        ExpiresIn=expires_in
    )
    return {
        "upload_url": upload_url,
        "file_key": file_key
    }


def generate_presigned_get_url(file_key: str, expires_in: int = 3600) -> Dict[str, str]:
    """Generate a presigned GET URL for downloads."""
    client = get_b2_client()
    download_url = client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.BUCKET_NAME,
            "Key": file_key
        },
        ExpiresIn=expires_in
    )
    return {
        "download_url": download_url,
        "file_key": file_key
    }
