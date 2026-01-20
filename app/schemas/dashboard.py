from pydantic import BaseModel
from typing import Optional

class DashboardStatsResponse(BaseModel):
    """Schema for admin dashboard summary statistics"""
    total_interests: int
    active_properties: int
    total_users: int
    total_investment: float
    
    # Growth/Status metrics
    interests_growth: Optional[str] = None
    properties_growth: Optional[str] = None
    users_growth: Optional[str] = None
    investment_growth: Optional[str] = None
