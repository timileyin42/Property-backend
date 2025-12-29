"""Schemas package initialization"""

from app.schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse
from app.schemas.user import UserCreate, UserUpdate, UserRoleUpdate, UserListResponse
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyResponse, PropertyListResponse
from app.schemas.investment import InvestmentCreate, InvestmentUpdate, InvestmentResponse, InvestmentDetailResponse, InvestmentListResponse
from app.schemas.update import UpdateCreate, UpdateResponse, UpdateListResponse

__all__ = [
    # Auth
    "SignupRequest",
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    # User
    "UserCreate",
    "UserUpdate",
    "UserRoleUpdate",
    "UserListResponse",
    # Property
    "PropertyCreate",
    "PropertyUpdate",
    "PropertyResponse",
    "PropertyListResponse",
    # Investment
    "InvestmentCreate",
    "InvestmentUpdate",
    "InvestmentResponse",
    "InvestmentDetailResponse",
    "InvestmentListResponse",
    # Update
    "UpdateCreate",
    "UpdateResponse",
    "UpdateListResponse",
]
