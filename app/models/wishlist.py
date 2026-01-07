from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Wishlist(Base):
    """User's saved/favorite properties"""
    
    __tablename__ = "wishlist"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Notification preferences for this property
    notify_on_update = Column(Boolean, default=True, nullable=False)
    notify_on_price_change = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="wishlist_items")
    property = relationship("Property")
    
    # Ensure a user can only save a property once
    __table_args__ = (
        UniqueConstraint('user_id', 'property_id', name='unique_user_property_wishlist'),
    )
    
    def __repr__(self):
        return f"<Wishlist(id={self.id}, user_id={self.user_id}, property_id={self.property_id})>"
