from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserCreate(BaseModel):
    """Schema for creating a user"""
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserRoleUpdate(BaseModel):
    """Schema for updating user role (admin only)"""
    role: UserRole


class UserResponse(BaseModel):
    """Response schema for user data"""
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    role: UserRole
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Response schema for paginated user list"""
    users: list[UserResponse]
    total: int
    page: int
    page_size: int
