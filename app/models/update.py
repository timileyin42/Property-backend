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
    image_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    related_property = relationship("Property", back_populates="updates")
    comments = relationship("UpdateComment", back_populates="update", cascade="all, delete-orphan")
    likes = relationship("UpdateLike", back_populates="update", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Update(id={self.id}, title={self.title})>"


class UpdateComment(Base):
    """Model for user comments on updates"""
    __tablename__ = "update_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    update_id = Column(Integer, ForeignKey("updates.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    update = relationship("Update", back_populates="comments")
    user = relationship("User", backref="update_comments")


class UpdateLike(Base):
    """Model for user likes on updates"""
    __tablename__ = "update_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    update_id = Column(Integer, ForeignKey("updates.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    update = relationship("Update", back_populates="likes")
    user = relationship("User", backref="update_likes")
