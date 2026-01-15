from fastapi import APIRouter, Depends, HTTPException, status
from app.core.permissions import require_admin, get_current_user
from app.models.user import User
from app.schemas.media import (
    UploadSignatureResponse,
    MediaUploadRequest,
    MediaDeleteRequest,
    MediaDeleteResponse
)
from app.services.cloudinary_service import (
    generate_image_upload_signature,
    generate_video_upload_signature,
    delete_media
)

router = APIRouter(prefix="/api/media", tags=["Media Upload"])


@router.post("/upload-signature", response_model=UploadSignatureResponse)
def get_upload_signature(
    request: MediaUploadRequest,
    current_user: User = Depends(require_admin)
):
    """
    Generate presigned upload signature for Cloudinary (Admin only)
    
    This endpoint returns the necessary parameters for the frontend to
    upload images/videos directly to Cloudinary without going through the backend.
    
    **Args:**
    - property_id: Optional property ID to organize uploads
    - resource_type: "image" or "video"
    - file_size_bytes: Optional file size in bytes (used to decide background uploads)
    
    **Returns:**
    - signature: Cloudinary signature for authentication
    - timestamp: Unix timestamp
    - api_key: Cloudinary API key
    - cloud_name: Cloudinary cloud name
    - folder: Upload folder path
    - upload_url: Cloudinary upload endpoint URL
    - background: Whether this upload should be treated as background (large files)
    """
    if request.resource_type == "video":
        signature_data = generate_video_upload_signature(request.property_id)
    else:
        signature_data = generate_image_upload_signature(request.property_id)
    
    is_large = bool(
        request.file_size_bytes is not None
        and request.file_size_bytes >= 10 * 1024 * 1024
    )
    
    return UploadSignatureResponse(
        **signature_data,
        background=is_large
    )


@router.post("/delete", response_model=MediaDeleteResponse)
def delete_media_file(
    request: MediaDeleteRequest,
    current_user: User = Depends(require_admin)
):
    """
    Delete a media file from Cloudinary (Admin only)
    
    **Args:**
    - public_id: The Cloudinary public ID of the file
    - resource_type: "image" or "video"
    
    **Returns:**
    - success: Whether deletion was successful
    - message: Status message
    - result: Cloudinary deletion result
    """
    result = delete_media(request.public_id, request.resource_type)
    
    if "error" in result:
        return MediaDeleteResponse(
            success=False,
            message=f"Failed to delete media: {result['error']}",
            result=result
        )
    
    return MediaDeleteResponse(
        success=True,
        message="Media deleted successfully",
        result=result
    )


@router.get("/upload-signature/image", response_model=UploadSignatureResponse)
def get_image_upload_signature(
    property_id: int = None,
    current_user: User = Depends(require_admin)
):
    """
    Quick endpoint to get image upload signature (Admin only)
    
    **Query params:**
    - property_id: Optional property ID
    
    **Returns:**
    Upload signature for images
    """
    signature_data = generate_image_upload_signature(property_id)
    return UploadSignatureResponse(**signature_data)


@router.get("/upload-signature/video", response_model=UploadSignatureResponse)
def get_video_upload_signature(
    property_id: int = None,
    current_user: User = Depends(require_admin)
):
    """
    Quick endpoint to get video upload signature (Admin only)
    
    **Query params:**
    - property_id: Optional property ID
    
    **Returns:**
    Upload signature for videos
    """
    signature_data = generate_video_upload_signature(property_id)
    return UploadSignatureResponse(**signature_data)
