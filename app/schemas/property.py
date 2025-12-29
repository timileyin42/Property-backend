from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.property import PropertyStatus


class PropertyCreate(BaseModel):
    """Schema for creating a property"""
    title: str = Field(..., min_length=3)
    location: str = Field(..., min_length=3)
    description: Optional[str] = None
    status: PropertyStatus = PropertyStatus.AVAILABLE
    image_urls: Optional[List[str]] = []
    
    # Fractional ownership (optional)
    total_fractions: Optional[int] = None
    fraction_price: Optional[float] = None
    project_value: Optional[float] = None


class PropertyUpdate(BaseModel):
    """Schema for updating property information"""
    title: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    status: Optional[PropertyStatus] = None
    image_urls: Optional[List[str]] = None
    
    # Fractional ownership updates
    total_fractions: Optional[int] = None
    fraction_price: Optional[float] = None
    project_value: Optional[float] = None


class PropertyResponse(BaseModel):
    """Response schema for property data"""
    id: int
    title: str
    location: str
    description: Optional[str]
    status: PropertyStatus
    image_urls: List[str]
    created_at: datetime
    updated_at: datetime
    
    # Fractional ownership
    total_fractions: Optional[int] = None
    fraction_price: Optional[float] = None
    project_value: Optional[float] = None
    fractions_sold: int = 0
    fractions_available: int = 0
    is_fractional: bool = False
    
    class Config:
        from_attributes = True


class PropertyListResponse(BaseModel):
    """Response schema for paginated property list"""
    properties: List[PropertyResponse]
    total: int
    page: int
    page_size: int
