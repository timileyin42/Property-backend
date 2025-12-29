from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class InquiryStatus(str, enum.Enum):
    """Inquiry status enumeration"""
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    CLOSED = "CLOSED"


class PropertyInquiry(Base):
    """Property inquiry/contact form submissions"""
    
    __tablename__ = "property_inquiries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Contact information
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    # Optional property reference
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="SET NULL"), nullable=True)
    
    # Status tracking
    status = Column(Enum(InquiryStatus), default=InquiryStatus.NEW, nullable=False, index=True)
    contacted_at = Column(DateTime(timezone=True), nullable=True)
    assigned_admin_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Metadata
    notes = Column(Text, nullable=True)  # Admin notes
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    property = relationship("Property")
    assigned_admin = relationship("User", foreign_keys=[assigned_admin_id])
    
    def __repr__(self):
        return f"<PropertyInquiry(id={self.id}, name={self.name}, status={self.status})>"
