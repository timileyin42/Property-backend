from sqlalchemy import Column, Integer, ForeignKey, DateTime, Float, Enum, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class DistributionStatus(str, enum.Enum):
    """Distribution payment status"""
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class EarningsDistribution(Base):
    """Earnings distribution records for investors"""
    
    __tablename__ = "earnings_distribution"
    
    id = Column(Integer, primary_key=True, index=True)
    property_revenue_id = Column(Integer, ForeignKey("property_revenue.id", ondelete="CASCADE"), nullable=False)
    investment_id = Column(Integer, ForeignKey("investments.id", ondelete="CASCADE"), nullable=False)
    
    # Snapshot of ownership at distribution time
    fractions_owned = Column(Integer, nullable=False)
    ownership_percentage = Column(Float, nullable=False)
    
    # Earnings calculation
    earnings_amount = Column(Float, nullable=False)
    
    # Payment tracking
    status = Column(Enum(DistributionStatus), default=DistributionStatus.PENDING, nullable=False)
    paid_date = Column(DateTime(timezone=True), nullable=True)
    payment_reference = Column(String, nullable=True)
    
    # Metadata
    notes = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    revenue = relationship("PropertyRevenue", back_populates="distributions")
    investment = relationship("Investment", back_populates="earnings_distributions")
    
    def __repr__(self):
        return f"<EarningsDistribution(id={self.id}, investment_id={self.investment_id}, amount={self.earnings_amount})>"
