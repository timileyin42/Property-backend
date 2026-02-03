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
    
    # Social stats
    likes_count: int = 0
    comments_count: int = 0
    is_liked_by_user: bool = False  # For authenticated requests
    
    class Config:
        from_attributes = True


class UpdateCommentCreate(BaseModel):
    """Schema for creating a comment"""
    content: str = Field(..., min_length=1)


class UpdateCommentResponse(BaseModel):
    """Schema for comment response"""
    id: int
    update_id: int
    user_id: int
    user_name: str
    user_avatar: Optional[str] = None  # If we have avatars later
    content: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CommentListResponse(BaseModel):
    """Paginated comments"""
    comments: list[UpdateCommentResponse]
    total: int
    page: int
    page_size: int


class UpdateListResponse(BaseModel):
    """Response schema for paginated update list"""
    updates: list[UpdateResponse]
    total: int
    page: int
    page_size: int
