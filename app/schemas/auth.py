from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from app.models.user import UserRole
import re


class SignupRequest(BaseModel):
    """Request schema for user signup"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = None
    
    @field_validator("full_name")
    def validate_full_name(cls, v):
        """Validate full_name to prevent spam and malicious content"""
        if not v or not v.strip():
            raise ValueError("Full name cannot be empty")
        
        # Check for URLs/links
        if re.search(r'(https?://|bit\.ly|tinyurl|ftp://|www\.)', v, re.IGNORECASE):
            raise ValueError("Full name cannot contain URLs or links")
        
        # Check for excessive special characters or emojis
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # Emoticons
            "\U0001F300-\U0001F5FF"  # Symbols & Pictographs
            "\U0001F680-\U0001F6FF"  # Transport & Map
            "\U0001F700-\U0001F77F"  # Alchemical Symbols
            "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
            "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            "\U0001FA00-\U0001FA6F"  # Chess Symbols
            "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001f926-\U0001f937"
            "\U00010000-\U0010ffff"
            "\u2640-\u2642"
            "\u2600-\u2B55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"  # dingbats
            "\u3030"
            "]+"
        )
        
        if emoji_pattern.search(v):
            raise ValueError("Full name cannot contain emojis or excessive special characters")
        
        # Allow only letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError("Full name can only contain letters, spaces, hyphens, and apostrophes")
        
        # Check for excessive spaces
        if "  " in v:
            raise ValueError("Full name cannot contain multiple consecutive spaces")
        
        return v.strip()
    
    @field_validator("phone")
    def validate_phone(cls, v):
        """Validate phone number format"""
        if v is None or v.strip() == "":
            return None
        
        # Check for URLs/links in phone
        if re.search(r'(https?://|bit\.ly|tinyurl|ftp://|www\.)', v, re.IGNORECASE):
            raise ValueError("Phone cannot contain URLs or links")
        
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)\+]', '', v)
        
        # Allow only digits (minimum 7, maximum 15 for international format)
        if not re.match(r'^\d{7,15}$', cleaned):
            raise ValueError("Phone must contain 7-15 digits")
        
        return v.strip()


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


class ForgotPasswordRequest(BaseModel):
    """Request schema for forgot password"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request schema for password reset"""
    email: EmailStr
    reset_code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)
