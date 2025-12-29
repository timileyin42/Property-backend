from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.distribution import DistributionStatus


class DistributionResponse(BaseModel):
    """Response schema for earnings distribution"""
    id: int
    property_revenue_id: int
    investment_id: int
    fractions_owned: int
    ownership_percentage: float
    earnings_amount: float
    status: DistributionStatus
    paid_date: Optional[datetime]
    payment_reference: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Nested data
    property_title: Optional[str] = None
    period_label: Optional[str] = None
    
    class Config:
        from_attributes = True


class DistributionStatusUpdate(BaseModel):
    """Schema for updating distribution status"""
    status: DistributionStatus
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


class DistributionListResponse(BaseModel):
    """Response schema for paginated distribution list"""
    distributions: list[DistributionResponse]
    total: int
    total_earnings: float
    total_paid: float
    total_pending: float


class InvestorEarningsSummary(BaseModel):
    """Summary of investor earnings"""
    total_earnings: float
    total_paid: float
    total_pending: float
    distributions_count: int
    properties_count: int
