from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Investment(Base):
    """Investment model linking users to properties with valuation tracking"""
    
    __tablename__ = "investments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    
    # Fractional ownership
    fractions_owned = Column(Integer, nullable=True)  # Number of fractions owned (null for non-fractional)
    
    initial_value = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="investments")
    property = relationship("Property", back_populates="investments")
    earnings_distributions = relationship("EarningsDistribution", back_populates="investment", cascade="all, delete-orphan")
    
    @property
    def ownership_percentage(self) -> float:
        """Calculate ownership percentage for fractional properties"""
        if self.fractions_owned and self.property and self.property.total_fractions:
            return (self.fractions_owned / self.property.total_fractions) * 100
        return 0.0
    
    @property
    def growth_percentage(self) -> float:
        """Calculate growth percentage"""
        if self.initial_value == 0:
            return 0.0
        return ((self.current_value - self.initial_value) / self.initial_value) * 100
    
    @property
    def growth_amount(self) -> float:
        """Calculate absolute growth amount"""
        return self.current_value - self.initial_value
    
    def __repr__(self):
        return f"<Investment(id={self.id}, user_id={self.user_id}, property_id={self.property_id})>"
