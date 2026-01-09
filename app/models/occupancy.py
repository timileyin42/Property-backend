from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class PropertyOccupancy(Base):
    """Property occupancy tracking for shortlet properties"""
    
    __tablename__ = "property_occupancy"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    
    # Period tracking
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    
    # Occupancy data
    nights_booked = Column(Integer, nullable=False)
    nights_available = Column(Integer, nullable=False)
    
    # Metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    related_property = relationship("Property", back_populates="occupancy_records")
    creator = relationship("User", foreign_keys=[created_by])
    
    @property
    def occupancy_rate(self) -> float:
        """Calculate occupancy rate percentage"""
        if self.nights_available == 0:
            return 0.0
        return (self.nights_booked / self.nights_available) * 100
    
    @property
    def period_label(self) -> str:
        """Get human-readable period label"""
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        return f"{months[self.month - 1]} {self.year}"
    
    def __repr__(self):
        return f"<PropertyOccupancy(id={self.id}, property_id={self.property_id}, period={self.period_label})>"
