from fastapi import APIRouter, HTTPException, status
from app.services.b2_service import generate_signed_download_url

router = APIRouter(tags=["Media Proxy"])


@router.get("/media/{file_key:path}")
def get_media_url(file_key: str):
    """Return a signed B2 download URL for a given file key."""
    try:
        url = generate_signed_download_url(file_key)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL"
        )
    return {"url": url}
