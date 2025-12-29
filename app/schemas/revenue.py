from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RevenueCreate(BaseModel):
    """Schema for creating revenue record"""
    property_id: int
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020)
    gross_revenue: float = Field(..., ge=0)
    expenses: float = Field(..., ge=0)
    notes: Optional[str] = None


class RevenueUpdate(BaseModel):
    """Schema for updating revenue record"""
    gross_revenue: Optional[float] = Field(None, ge=0)
    expenses: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class RevenueResponse(BaseModel):
    """Response schema for revenue data"""
    id: int
    property_id: int
    month: int
    year: int
    gross_revenue: float
    expenses: float
    net_income: float
    profit_margin: float
    period_label: str
    distributed: bool
    distribution_date: Optional[datetime]
    notes: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RevenueListResponse(BaseModel):
    """Response schema for paginated revenue list"""
    revenue_records: list[RevenueResponse]
    total: int
    total_gross_revenue: float
    total_expenses: float
    total_net_income: float


class DistributeRevenueRequest(BaseModel):
    """Request schema for distributing revenue"""
    revenue_id: int
