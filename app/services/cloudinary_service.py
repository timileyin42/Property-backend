"""
Cloudinary service for media uploads
Handles presigned URL generation for secure direct uploads
"""

import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.utils import cloudinary_url
from app.core.config import settings
from typing import Dict, Any, Optional
import time
import hashlib


# Initialize Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)


def generate_upload_signature(
    folder: str = None,
    resource_type: str = "image",
    allowed_formats: list = None,
    max_file_size: int = None
) -> Dict[str, Any]:
    """
    Generate presigned upload parameters for Cloudinary
    
    Args:
        folder: Optional folder path in Cloudinary
        resource_type: Type of resource (image, video, raw, auto)
        allowed_formats: List of allowed file formats (e.g., ['jpg', 'png', 'mp4'])
    
    Returns:
        Dictionary containing upload parameters and signature
    """
    timestamp = int(time.time())
    
    # Build upload parameters
    upload_params = {
        "timestamp": timestamp,
        "folder": folder or settings.CLOUDINARY_UPLOAD_FOLDER,
    }
    
    # Add allowed formats if specified
    if allowed_formats:
        upload_params["allowed_formats"] = ",".join(allowed_formats)
    # Add max_file_size if specified (not a signable param for Cloudinary)
    if max_file_size:
        upload_params["max_file_size"] = max_file_size
    
    # Add resource type specific parameters
    # Note: resource_type is NOT included in signature when part of the URL
    # We only add it to params for frontend info, but remove before signing if needed
    
    params_to_sign = upload_params.copy()
    # Cloudinary ignores max_file_size in signature verification
    params_to_sign.pop("max_file_size", None)
    
    if resource_type == "video":
        # Don't add resource_type to params_to_sign as it's in the URL
        # Don't add chunk_size to params_to_sign unless frontend explicitly sends it
        pass
    
    # Generate signature
    signature = cloudinary.utils.api_sign_request(
        params_to_sign,
        settings.CLOUDINARY_API_SECRET
    )
    
    # Return complete upload configuration
    return {
        "signature": signature,
        "timestamp": timestamp,
        "api_key": settings.CLOUDINARY_API_KEY,
        "cloud_name": settings.CLOUDINARY_CLOUD_NAME,
        "folder": upload_params["folder"],
        "upload_url": f"https://api.cloudinary.com/v1_1/{settings.CLOUDINARY_CLOUD_NAME}/{resource_type}/upload",
        **upload_params,
        # Add video specific params back to response for frontend to use if needed
        **({"resource_type": "video", "chunk_size": 6000000} if resource_type == "video" else {})
    }


def generate_image_upload_signature(property_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Generate presigned URL parameters for image uploads
    
    Args:
        property_id: Optional property ID to organize uploads
    
    Returns:
        Upload configuration with signature
    """
    folder = f"{settings.CLOUDINARY_UPLOAD_FOLDER}/properties"
    if property_id:
        folder = f"{folder}/{property_id}"
    
    # Allow all common image formats from iOS, Android, and web
    # Set max_file_size to 100MB for images
    return generate_upload_signature(
        folder=folder,
        resource_type="image",
        allowed_formats=[
            "jpg", "jpeg", "png", "webp", "gif", "heic", "heif", "heif-sequence", "heic-sequence"
        ],
        max_file_size=100 * 1024 * 1024  # 100MB
    )


def generate_video_upload_signature(property_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Generate presigned URL parameters for video uploads
    
    Args:
        property_id: Optional property ID to organize uploads
    
    Returns:
        Upload configuration with signature
    """
    folder = f"{settings.CLOUDINARY_UPLOAD_FOLDER}/properties"
    if property_id:
        folder = f"{folder}/{property_id}"
    
    # Allow all common video formats from iOS, Android, and web
    # Set max_file_size to 1GB for videos
    return generate_upload_signature(
        folder=folder,
        resource_type="video",
        allowed_formats=[
            "mp4", "webm", "ogg", "mov", "3gp", "3g2", "x-m4v", "avi", "mkv", "quicktime"
        ],
        max_file_size=1024 * 1024 * 1024  # 1GB
    )


def delete_media(public_id: str, resource_type: str = "image") -> Dict[str, Any]:
    """
    Delete a media file from Cloudinary
    
    Args:
        public_id: The public ID of the media to delete
        resource_type: Type of resource (image, video)
    
    Returns:
        Deletion result
    """
    try:
        result = cloudinary.uploader.destroy(
            public_id,
            resource_type=resource_type,
            invalidate=True
        )
        return result
    except Exception as e:
        return {"error": str(e)}


def get_optimized_url(
    public_id: str,
    width: int = None,
    height: int = None,
    crop: str = "fill",
    quality: str = "auto",
    format: str = "auto"
) -> str:
    """
    Generate optimized URL for an image
    
    Args:
        public_id: The public ID of the image
        width: Desired width
        height: Desired height
        crop: Crop mode (fill, fit, scale, etc.)
        quality: Quality setting (auto, best, good, etc.)
        format: Format (auto, jpg, png, webp, etc.)
    
    Returns:
        Optimized image URL
    """
    transformation = {
        "quality": quality,
        "fetch_format": format
    }
    
    if width:
        transformation["width"] = width
    if height:
        transformation["height"] = height
    if width or height:
        transformation["crop"] = crop
    
    url, _ = cloudinary_url(
        public_id,
        **transformation
    )
    
    return url


def extract_public_id_from_url(cloudinary_url: str) -> Optional[str]:
    """
    Extract public ID from Cloudinary URL
    
    Args:
        cloudinary_url: Full Cloudinary URL
    
    Returns:
        Public ID or None
    """
    try:
        # Example URL: https://res.cloudinary.com/cloud_name/image/upload/v1234567890/folder/image.jpg
        parts = cloudinary_url.split("/upload/")
        if len(parts) == 2:
            # Get everything after /upload/ and remove version
            path = parts[1]
            # Remove version (v1234567890)
            if path.startswith("v"):
                path = "/".join(path.split("/")[1:])
            # Remove file extension
            public_id = path.rsplit(".", 1)[0]
            return public_id
    except Exception:
        pass
    return None
