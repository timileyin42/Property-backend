"""
Cloudflare R2 helpers for signed upload and download URLs.
"""

import logging
from typing import Dict
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from app.core.config import settings

_r2_client = None
_logger = logging.getLogger(__name__)


def get_r2_client():
    global _r2_client
    if _r2_client is None:
        _r2_client = boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4")
        )
        _logger.info("R2 client initialized for bucket: %s", settings.R2_BUCKET_NAME)
    return _r2_client


def generate_presigned_put_url(file_key: str, content_type: str, expires_in: int = 3600) -> Dict[str, str]:
    client = get_r2_client()
    url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.R2_BUCKET_NAME,
            "Key": file_key,
            "ContentType": content_type
        },
        ExpiresIn=expires_in
    )
    return {
        "upload_url": url,
        "file_key": file_key,
        "upload_headers": {
            "Content-Type": content_type
        }
    }


def generate_signed_download_url(file_key: str, expires_in: int = 3600) -> str:
    client = get_r2_client()
    try:
        client.head_object(Bucket=settings.R2_BUCKET_NAME, Key=file_key)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey"}:
            raise FileNotFoundError("File not found") from exc
        raise
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.R2_BUCKET_NAME,
            "Key": file_key
        },
        ExpiresIn=expires_in
    )


def generate_presigned_get_url(file_key: str, expires_in: int = 3600) -> Dict[str, str]:
    download_url = generate_signed_download_url(file_key, expires_in=expires_in)
    return {
        "download_url": download_url,
        "file_key": file_key
    }
