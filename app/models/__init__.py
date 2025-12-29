"""Models package initialization"""

from app.models.user import User, UserRole
from app.models.property import Property, PropertyStatus
from app.models.investment import Investment
from app.models.update import Update
from app.models.occupancy import PropertyOccupancy
from app.models.revenue import PropertyRevenue
from app.models.distribution import EarningsDistribution, DistributionStatus
from app.models.inquiry import PropertyInquiry, InquiryStatus

__all__ = [
    "User",
    "UserRole",
    "Property",
    "PropertyStatus",
    "Investment",
    "Update",
    "PropertyOccupancy",
    "PropertyRevenue",
    "EarningsDistribution",
    "DistributionStatus",
    "PropertyInquiry",
    "InquiryStatus",
]
