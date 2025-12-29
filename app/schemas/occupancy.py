from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OccupancyCreate(BaseModel):
    """Schema for creating occupancy record"""
    property_id: int
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020)
    nights_booked: int = Field(..., ge=0)
    nights_available: int = Field(..., gt=0)
    notes: Optional[str] = None


class OccupancyUpdate(BaseModel):
    """Schema for updating occupancy record"""
    nights_booked: Optional[int] = Field(None, ge=0)
    nights_available: Optional[int] = Field(None, gt=0)
    notes: Optional[str] = None


class OccupancyResponse(BaseModel):
    """Response schema for occupancy data"""
    id: int
    property_id: int
    month: int
    year: int
    nights_booked: int
    nights_available: int
    occupancy_rate: float
    period_label: str
    notes: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OccupancyListResponse(BaseModel):
    """Response schema for paginated occupancy list"""
    occupancy_records: list[OccupancyResponse]
    total: int
    average_occupancy_rate: float
