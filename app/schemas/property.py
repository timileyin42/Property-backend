from pydantic import BaseModel, Field, field_validator, model_validator
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
    video_urls: Optional[List[str]] = []
    
    # Property details (optional)
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area_sqft: Optional[float] = None
    expected_roi: Optional[float] = None
    is_off_plan: Optional[bool] = False
    off_plan_duration_months: Optional[int] = None
    
    # Fractional ownership (optional)
    total_fractions: Optional[int] = None
    fraction_price: Optional[float] = None
    project_value: Optional[float] = None

    # off_plan_duration_months is optional in updates; no enforcement here


class PropertyUpdate(BaseModel):
    """Schema for updating property information"""
    title: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    status: Optional[PropertyStatus] = None
    image_urls: Optional[List[str]] = None
    video_urls: Optional[List[str]] = None
    
    # Property details updates
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area_sqft: Optional[float] = None
    expected_roi: Optional[float] = None
    is_off_plan: Optional[bool] = None
    off_plan_duration_months: Optional[int] = None
    
    # Fractional ownership updates
    total_fractions: Optional[int] = None
    fraction_price: Optional[float] = None
    project_value: Optional[float] = None

    @model_validator(mode="after")
    def validate_off_plan(self):
        if self.off_plan_duration_months is not None and self.off_plan_duration_months <= 0:
            raise ValueError("off_plan_duration_months must be greater than 0")
        if self.is_off_plan is True and self.off_plan_duration_months is None:
            raise ValueError("off_plan_duration_months is required when is_off_plan is true")
        if self.is_off_plan is False and self.off_plan_duration_months is not None:
            raise ValueError("off_plan_duration_months is only allowed when is_off_plan is true")
        return self


class PropertyResponse(BaseModel):
    """Response schema for property data"""
    id: int
    title: str
    location: str
    description: Optional[str]
    status: PropertyStatus
    image_urls: List[str] = []
    primary_image: Optional[str] = None
    video_urls: List[str] = []
    created_at: datetime
    updated_at: datetime
    
    # Property details
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area_sqft: Optional[float] = None
    expected_roi: Optional[float] = None
    is_off_plan: bool = False
    off_plan_duration_months: Optional[int] = None
    
    # Fractional ownership
    total_fractions: Optional[int] = None
    fraction_price: Optional[float] = None
    project_value: Optional[float] = None
    fractions_sold: int = 0
    fractions_available: int = 0
    is_fractional: bool = False
    
    class Config:
        from_attributes = True

    @field_validator("image_urls", "video_urls", mode="before")
    @classmethod
    def normalize_media_lists(cls, v):
        return v or []


class PropertyListResponse(BaseModel):
    """Response schema for paginated property list"""
    properties: List[PropertyResponse]
    total: int
    page: int
    page_size: int
