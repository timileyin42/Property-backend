from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UpdateCreate(BaseModel):
    """Schema for creating a property update/news"""
    property_id: Optional[int] = None
    title: str = Field(..., min_length=3)
    content: str = Field(..., min_length=10)
    image_url: Optional[str] = None


class UpdateUpdate(BaseModel):
    """Schema for updating a property update/news"""
    property_id: Optional[int] = None
    title: Optional[str] = Field(None, min_length=3)
    content: Optional[str] = Field(None, min_length=10)
    image_url: Optional[str] = None


class UpdateResponse(BaseModel):
    """Response schema for update data"""
    id: int
    property_id: Optional[int]
    title: str
    content: str
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Optional property info
    property_title: Optional[str] = None
    
    class Config:
        from_attributes = True


class UpdateListResponse(BaseModel):
    """Response schema for paginated update list"""
    updates: list[UpdateResponse]
    total: int
    page: int
    page_size: int
