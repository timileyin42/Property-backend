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
    allowed_formats: list = None
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
    
    # Add resource type specific parameters
    if resource_type == "video":
        upload_params["resource_type"] = "video"
        upload_params["chunk_size"] = 6000000  # 6MB chunks for large videos
    
    # Generate signature
    signature = cloudinary.utils.api_sign_request(
        upload_params,
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
        **upload_params
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
    
    return generate_upload_signature(
        folder=folder,
        resource_type="image",
        allowed_formats=["jpg", "jpeg", "png", "webp", "gif"]
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
    
    return generate_upload_signature(
        folder=folder,
        resource_type="video",
        allowed_formats=["mp4", "mov", "avi", "webm", "mkv"]
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
