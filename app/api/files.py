from fastapi import APIRouter, Depends
from app.core.permissions import require_admin
from app.models.user import User
from app.schemas.files import (
    PresignUploadRequest,
    PresignUploadResponse,
    PresignDownloadRequest,
    PresignDownloadResponse
)
from app.services.b2_service import (
    generate_presigned_put_url,
    generate_presigned_get_url
)

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/presign-upload", response_model=PresignUploadResponse)
def presign_upload(
    request: PresignUploadRequest,
    current_user: User = Depends(require_admin)
):
    """Generate a presigned upload URL (Admin only)."""
    return generate_presigned_put_url(request.filename, request.content_type)


@router.post("/presign-download", response_model=PresignDownloadResponse)
def presign_download(request: PresignDownloadRequest):
    """Generate a presigned download URL (public)."""
    return generate_presigned_get_url(request.file_key)
