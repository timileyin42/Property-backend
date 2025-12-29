from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class PropertyRevenue(Base):
    """Property revenue and expense tracking"""
    
    __tablename__ = "property_revenue"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    
    # Period tracking
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    
    # Financial data
    gross_revenue = Column(Float, nullable=False)
    expenses = Column(Float, nullable=False)
    
    # Distribution tracking
    distributed = Column(Boolean, default=False, nullable=False)
    distribution_date = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    property = relationship("Property", back_populates="revenue_records")
    creator = relationship("User", foreign_keys=[created_by])
    distributions = relationship("EarningsDistribution", back_populates="revenue", cascade="all, delete-orphan")
    
    @property
    def net_income(self) -> float:
        """Calculate net distributable income"""
        return self.gross_revenue - self.expenses
    
    @property
    def period_label(self) -> str:
        """Get human-readable period label"""
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return f"{months[self.month - 1]} {self.year}"
    
    @property
    def profit_margin(self) -> float:
        """Calculate profit margin percentage"""
        if self.gross_revenue == 0:
            return 0.0
        return (self.net_income / self.gross_revenue) * 100
    
    def __repr__(self):
        return f"<PropertyRevenue(id={self.id}, property_id={self.property_id}, period={self.period_label})>"
