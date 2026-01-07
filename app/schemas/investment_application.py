from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.investment_application import ApplicationStatus


class InvestmentApplicationCreate(BaseModel):
    """Schema for creating investment application"""
    motivation: str = Field(..., min_length=50, max_length=2000)
    investment_amount: Optional[float] = Field(None, gt=0)
    experience: Optional[str] = Field(None, max_length=2000)


class InvestmentApplicationUpdate(BaseModel):
    """Schema for user updating their application (before review)"""
    motivation: Optional[str] = Field(None, min_length=50, max_length=2000)
    investment_amount: Optional[float] = Field(None, gt=0)
    experience: Optional[str] = Field(None, max_length=2000)


class InvestmentApplicationReview(BaseModel):
    """Schema for admin reviewing application"""
    status: ApplicationStatus
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class InvestmentApplicationResponse(BaseModel):
    """Response schema for investment application"""
    id: int
    user_id: int
    motivation: str
    investment_amount: Optional[float]
    experience: Optional[str]
    status: ApplicationStatus
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    admin_notes: Optional[str]
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Enriched data
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    reviewer_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class InvestmentApplicationListResponse(BaseModel):
    """Response schema for paginated applications"""
    applications: list[InvestmentApplicationResponse]
    total: int
    pending_count: int
    approved_count: int
    rejected_count: int
