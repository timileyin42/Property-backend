from pydantic import BaseModel
from typing import Dict


class PresignUploadRequest(BaseModel):
    """Request schema for presigned upload URL"""
    filename: str
    content_type: str


class PresignUploadResponse(BaseModel):
    """Response schema for presigned upload URL"""
    upload_url: str
    file_key: str
    upload_headers: Dict[str, str]


class PresignDownloadRequest(BaseModel):
    """Request schema for presigned download URL"""
    file_key: str


class PresignDownloadResponse(BaseModel):
    """Response schema for presigned download URL"""
    download_url: str
    file_key: str
