from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class SignupRequest(BaseModel):
    """Request schema for user signup"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    """Request schema for user login"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response schema for authentication tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Response schema for user data"""
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    role: str
    is_verified: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True
