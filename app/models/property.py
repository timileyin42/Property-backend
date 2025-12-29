from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class PropertyStatus(str, enum.Enum):
    """Property status enumeration"""
    AVAILABLE = "AVAILABLE"
    SOLD = "SOLD"
    INVESTED = "INVESTED"


class Property(Base):
    """Property model for real estate listings"""
    
    __tablename__ = "properties"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    location = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(PropertyStatus), default=PropertyStatus.AVAILABLE, nullable=False)
    image_urls = Column(ARRAY(String), nullable=True, default=[])
    
    # Fractional ownership fields
    total_fractions = Column(Integer, nullable=True)  # Total fractions available
    fraction_price = Column(Float, nullable=True)  # Price per fraction
    project_value = Column(Float, nullable=True)  # Total project value
    fractions_sold = Column(Integer, default=0, nullable=False)  # Fractions already sold
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    investments = relationship("Investment", back_populates="property", cascade="all, delete-orphan")
    updates = relationship("Update", back_populates="property", cascade="all, delete-orphan")
    occupancy_records = relationship("PropertyOccupancy", back_populates="property", cascade="all, delete-orphan")
    revenue_records = relationship("PropertyRevenue", back_populates="property", cascade="all, delete-orphan")
    
    @property
    def fractions_available(self) -> int:
        """Calculate available fractions"""
        if self.total_fractions is None:
            return 0
        return self.total_fractions - self.fractions_sold
    
    @property
    def is_fractional(self) -> bool:
        """Check if property uses fractional ownership"""
        return self.total_fractions is not None and self.total_fractions > 0
    
    def __repr__(self):
        return f"<Property(id={self.id}, title={self.title}, status={self.status})>"
