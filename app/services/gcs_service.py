"""
Google Cloud Storage helpers for signed upload and download URLs.
"""

import base64
import json
import logging
from datetime import timedelta
from typing import Dict
from google.cloud import storage
from google.oauth2 import service_account
from app.core.config import settings

_gcs_client = None
_gcs_bucket = None
_logger = logging.getLogger(__name__)


def _load_service_account_info() -> dict:
    """Decode the base64 service account JSON from env."""
    if not settings.GCP_SERVICE_ACCOUNT_KEY_BASE64:
        raise ValueError("GCP_SERVICE_ACCOUNT_KEY_BASE64 is not configured")
    decoded = base64.b64decode(settings.GCP_SERVICE_ACCOUNT_KEY_BASE64).decode("utf-8")
    return json.loads(decoded)


def get_gcs_client() -> storage.Client:
    """Create or return a cached GCS client using service account credentials."""
    global _gcs_client
    if _gcs_client is None:
        info = _load_service_account_info()
        credentials = service_account.Credentials.from_service_account_info(info)
        _gcs_client = storage.Client(credentials=credentials)
        _logger.info("GCS client initialized for project: %s", info.get("project_id"))
    return _gcs_client


def get_gcs_bucket() -> storage.Bucket:
    """Get the configured GCS bucket instance."""
    global _gcs_bucket
    if _gcs_bucket is None:
        _gcs_bucket = get_gcs_client().bucket(settings.GCP_BUCKET_NAME)
    return _gcs_bucket


def generate_presigned_put_url(file_key: str, content_type: str, expires_in: int = 3600) -> Dict[str, str]:
    """Generate a signed PUT URL for uploads."""
    bucket = get_gcs_bucket()
    blob = bucket.blob(file_key)
    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(seconds=expires_in),
        method="PUT",
        content_type=content_type
    )
    return {
        "upload_url": url,
        "file_key": file_key,
        "upload_headers": {
            "Content-Type": content_type
        }
    }


def generate_signed_download_url(file_key: str, expires_in: int = 3600) -> str:
    """Generate a signed GET URL for private files."""
    bucket = get_gcs_bucket()
    blob = bucket.blob(file_key)
    if not blob.exists(get_gcs_client()):
        raise FileNotFoundError("File not found")
    return blob.generate_signed_url(
        version="v4",
        expiration=timedelta(seconds=expires_in),
        method="GET"
    )


def generate_presigned_get_url(file_key: str, expires_in: int = 3600) -> Dict[str, str]:
    """Return a signed GET URL for downloads."""
    download_url = generate_signed_download_url(file_key, expires_in=expires_in)
    return {
        "download_url": download_url,
        "file_key": file_key
    }
