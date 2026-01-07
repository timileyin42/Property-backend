from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    """User role enumeration"""
    PUBLIC = "PUBLIC"
    USER = "USER"
    INVESTOR = "INVESTOR"
    ADMIN = "ADMIN"


class User(Base):
    """User model for authentication and authorization"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    
    # Email verification
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String, nullable=True)  # OTP code
    verification_token_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Password reset
    password_reset_token = Column(String, nullable=True)  # Reset code
    password_reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    investments = relationship("Investment", back_populates="user", cascade="all, delete-orphan")
    inquiries = relationship("PropertyInquiry", back_populates="user", foreign_keys="PropertyInquiry.user_id", cascade="all, delete-orphan")
    wishlist_items = relationship("Wishlist", back_populates="user", cascade="all, delete-orphan")
    investment_applications = relationship("InvestmentApplication", back_populates="user", foreign_keys="InvestmentApplication.user_id", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
