from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Update(Base):
    """Update/news model for property-related announcements"""
    
    __tablename__ = "updates"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=True)
    
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    property = relationship("Property", back_populates="updates")
    
    def __repr__(self):
        return f"<Update(id={self.id}, title={self.title})>"
