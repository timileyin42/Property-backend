from pydantic import BaseModel
from typing import Optional, List


class UploadSignatureResponse(BaseModel):
    """Response schema for upload signature"""
    signature: str
    timestamp: int
    api_key: str
    cloud_name: str
    folder: str
    upload_url: str
    resource_type: Optional[str] = None
    allowed_formats: Optional[str] = None


class MediaUploadRequest(BaseModel):
    """Request schema for media upload signature"""
    property_id: Optional[int] = None
    resource_type: str = "image"  # image or video


class MediaDeleteRequest(BaseModel):
    """Request schema for deleting media"""
    public_id: str
    resource_type: str = "image"  # image or video


class MediaDeleteResponse(BaseModel):
    """Response schema for media deletion"""
    success: bool
    message: str
    result: Optional[dict] = None
