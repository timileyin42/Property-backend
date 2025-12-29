from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class InvestmentCreate(BaseModel):
    """Schema for creating an investment (admin only)"""
    user_id: int
    property_id: int
    fractions_owned: Optional[int] = None  # For fractional properties
    initial_value: float = Field(..., gt=0)
    current_value: float = Field(..., gt=0)


class InvestmentUpdate(BaseModel):
    """Schema for updating investment valuation"""
    current_value: float = Field(..., gt=0)


class InvestmentResponse(BaseModel):
    """Response schema for investment data"""
    id: int
    user_id: int
    property_id: int
    fractions_owned: Optional[int] = None
    ownership_percentage: float = 0.0
    initial_value: float
    current_value: float
    growth_percentage: float
    growth_amount: float
    created_at: datetime
    updated_at: datetime
    
    # Nested property info
    property_title: Optional[str] = None
    property_location: Optional[str] = None
    
    class Config:
        from_attributes = True


class InvestmentDetailResponse(BaseModel):
    """Detailed response schema for investment with full property info"""
    id: int
    user_id: int
    property_id: int
    initial_value: float
    current_value: float
    growth_percentage: float
    growth_amount: float
    created_at: datetime
    updated_at: datetime
    
    # Full property object
    property: dict
    
    class Config:
        from_attributes = True


class InvestmentListResponse(BaseModel):
    """Response schema for paginated investment list"""
    investments: list[InvestmentResponse]
    total: int
    total_initial_value: float
    total_current_value: float
    total_growth_percentage: float
