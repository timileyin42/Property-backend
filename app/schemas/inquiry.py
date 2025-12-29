from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.inquiry import InquiryStatus


class InquiryCreate(BaseModel):
    """Schema for creating an inquiry"""
    name: str = Field(..., min_length=2)
    email: EmailStr
    phone: str = Field(..., min_length=10)
    message: str = Field(..., min_length=10)
    property_id: Optional[int] = None


class InquiryUpdate(BaseModel):
    """Schema for updating inquiry (admin only)"""
    status: Optional[InquiryStatus] = None
    assigned_admin_id: Optional[int] = None
    notes: Optional[str] = None


class InquiryResponse(BaseModel):
    """Response schema for inquiry data"""
    id: int
    name: str
    email: str
    phone: str
    message: str
    property_id: Optional[int]
    status: InquiryStatus
    contacted_at: Optional[datetime]
    assigned_admin_id: Optional[int]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Nested data
    property_title: Optional[str] = None
    assigned_admin_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class InquiryListResponse(BaseModel):
    """Response schema for paginated inquiry list"""
    inquiries: list[InquiryResponse]
    total: int
    new_count: int
    contacted_count: int
    closed_count: int
