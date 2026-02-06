"""
Backblaze B2 native SDK helpers for upload and download URLs.
"""

from typing import Dict
from b2sdk.v2 import InMemoryAccountInfo, B2Api
from app.core.config import settings

_b2_api = None
_b2_bucket = None


def get_b2_api() -> B2Api:
    """Create or return a cached B2 API client."""
    global _b2_api
    if _b2_api is None:
        info = InMemoryAccountInfo()
        _b2_api = B2Api(info)
        _b2_api.authorize_account(
            "production",
            settings.B2_ACCOUNT_ID,
            settings.B2_APPLICATION_KEY
        )
    return _b2_api


def get_b2_bucket():
    """Get the configured B2 bucket instance."""
    global _b2_bucket
    if _b2_bucket is None:
        _b2_bucket = get_b2_api().get_bucket_by_name(settings.B2_BUCKET_NAME)
    return _b2_bucket


def generate_presigned_put_url(file_key: str, content_type: str, expires_in: int = 3600) -> Dict[str, str]:
    """Generate an upload URL and required headers for B2 uploads."""
    bucket = get_b2_bucket()
    upload_url_response = get_b2_api().session.get_upload_url(bucket.id_)
    upload_url = getattr(upload_url_response, "upload_url", None) or upload_url_response.get("uploadUrl")
    auth_token = getattr(upload_url_response, "authorization_token", None) or upload_url_response.get("authorizationToken")
    return {
        "upload_url": upload_url,
        "file_key": file_key,
        "upload_headers": {
            "Authorization": auth_token,
            "X-Bz-File-Name": file_key,
            "Content-Type": content_type,
            "X-Bz-Content-Sha1": "do_not_verify"
        }
    }


def generate_presigned_get_url(file_key: str, expires_in: int = 3600) -> Dict[str, str]:
    """Generate a signed download URL for private files."""
    bucket = get_b2_bucket()
    token = bucket.get_download_authorization(
        file_name_prefix="",
        valid_duration_in_seconds=expires_in
    )
    download_url = (
        f"{settings.B2_DOWNLOAD_URL}/file/{settings.B2_BUCKET_NAME}/{file_key}"
        f"?Authorization={token}"
    )
    return {
        "download_url": download_url,
        "file_key": file_key
    }
