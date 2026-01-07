from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WishlistCreate(BaseModel):
    """Schema for adding property to wishlist"""
    property_id: int
    notify_on_update: bool = True
    notify_on_price_change: bool = True


class WishlistUpdate(BaseModel):
    """Schema for updating wishlist preferences"""
    notify_on_update: Optional[bool] = None
    notify_on_price_change: Optional[bool] = None


class WishlistResponse(BaseModel):
    """Response schema for wishlist item"""
    id: int
    user_id: int
    property_id: int
    notify_on_update: bool
    notify_on_price_change: bool
    created_at: datetime
    
    # Property details (enriched)
    property_title: Optional[str] = None
    property_location: Optional[str] = None
    property_status: Optional[str] = None
    property_image: Optional[str] = None
    
    class Config:
        from_attributes = True


class WishlistListResponse(BaseModel):
    """Response schema for paginated wishlist"""
    items: list[WishlistResponse]
    total: int
