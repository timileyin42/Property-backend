from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.permissions import get_current_user_optional
from app.models.user import User
from app.models.property import Property, PropertyStatus
from app.models.update import Update, UpdateComment, UpdateLike
from app.schemas.property import PropertyResponse, PropertyListResponse
from app.schemas.update import UpdateResponse, UpdateListResponse, CommentListResponse, UpdateCommentResponse

router = APIRouter(prefix="/api", tags=["Public"])


@router.get("/properties", response_model=PropertyListResponse)
def get_properties(
    page: int = 1,
    page_size: int = 10,
    status: Optional[PropertyStatus] = PropertyStatus.AVAILABLE,
    db: Session = Depends(get_db)
):
    """
    Get list of properties
    
    By default, only shows AVAILABLE properties.
    Supports pagination.
    """
    query = db.query(Property)
    
    # Filter by status if provided
    if status:
        query = query.filter(Property.status == status)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    skip = (page - 1) * page_size
    properties = query.order_by(Property.created_at.desc()).offset(skip).limit(page_size).all()
    
    # Enrich with primary image URL
    for property in properties:
        property.primary_image = property.image_urls[0] if property.image_urls else None
    
    return PropertyListResponse(
        properties=properties,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/properties/{property_id}", response_model=PropertyResponse)
def get_property(property_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific property
    """
    property = db.query(Property).filter(Property.id == property_id).first()
    
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Enrich with primary image URL
    property.primary_image = property.image_urls[0] if property.image_urls else None
    
    return property


@router.get("/updates", response_model=UpdateListResponse)
def get_updates(
    page: int = 1,
    page_size: int = 10,
    property_id: Optional[int] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get list of property updates/news (public endpoint)
    
    Optionally filter by property_id.
    Supports pagination.
    """
    query = db.query(Update)
    
    # Filter by property if provided
    if property_id:
        query = query.filter(Update.property_id == property_id)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    skip = (page - 1) * page_size
    updates = query.order_by(Update.created_at.desc()).offset(skip).limit(page_size).all()
    
    # Enrich with property titles and social stats
    for update in updates:
        if update.property_id:
            property = db.query(Property).filter(Property.id == update.property_id).first()
            if property:
                update.property_title = property.title
        
        # Count likes and comments
        update.likes_count = db.query(UpdateLike).filter(UpdateLike.update_id == update.id).count()
        update.comments_count = db.query(UpdateComment).filter(UpdateComment.update_id == update.id).count()
        
        # Check if liked by current user
        if current_user:
            is_liked = db.query(UpdateLike).filter(
                UpdateLike.update_id == update.id,
                UpdateLike.user_id == current_user.id
            ).first()
            update.is_liked_by_user = bool(is_liked)
        else:
            update.is_liked_by_user = False
    
    return UpdateListResponse(
        updates=updates,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/updates/{update_id}", response_model=UpdateResponse)
def get_update(
    update_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific update
    """
    update = db.query(Update).filter(Update.id == update_id).first()
    
    if not update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Update not found"
        )
    
    # Enrich with property title if exists
    if update.property_id:
        property = db.query(Property).filter(Property.id == update.property_id).first()
        if property:
            update.property_title = property.title
    
    # Count likes and comments
    update.likes_count = db.query(UpdateLike).filter(UpdateLike.update_id == update.id).count()
    update.comments_count = db.query(UpdateComment).filter(UpdateComment.update_id == update.id).count()
    
    # Check if liked by current user
    if current_user:
        is_liked = db.query(UpdateLike).filter(
            UpdateLike.update_id == update.id,
            UpdateLike.user_id == current_user.id
        ).first()
        update.is_liked_by_user = bool(is_liked)
    else:
        update.is_liked_by_user = False
        
    return update


@router.get("/updates/{update_id}/comments", response_model=CommentListResponse)
def get_public_update_comments(
    update_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get comments for an update (Public)
    """
    # Verify update exists
    update = db.query(Update).filter(Update.id == update_id).first()
    if not update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Update not found"
        )
        
    query = db.query(UpdateComment).filter(UpdateComment.update_id == update_id)
    total = query.count()
    
    skip = (page - 1) * page_size
    comments = query.order_by(UpdateComment.created_at.desc()).offset(skip).limit(page_size).all()
    
    # Enrich comments with user info
    for comment in comments:
        if comment.user:
            comment.user_name = comment.user.full_name or "User"
            # comment.user_avatar = comment.user.avatar_url 
    
    return CommentListResponse(
        comments=comments,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/contact", status_code=status.HTTP_201_CREATED)
def express_interest(
    name: str = Body(...),
    email: str = Body(...),
    phone: str = Body(...),
    message: str = Body(...),
    property_id: Optional[int] = Body(None),
    db: Session = Depends(get_db)
):
    """
    Submit contact/express interest form
    
    Stores inquiry in database and sends email notifications:
    - Admin notification email
    - User acknowledgement email
    """
    from app.models.inquiry import PropertyInquiry
    from app.services.email_service import (
        send_inquiry_admin_notification,
        send_inquiry_user_acknowledgement
    )
    
    # Verify property exists if property_id provided
    property_title = None
    if property_id:
        property = db.query(Property).filter(Property.id == property_id).first()
        if property:
            property_title = property.title
    
    # Create inquiry record
    inquiry = PropertyInquiry(
        name=name,
        email=email,
        phone=phone,
        message=message,
        property_id=property_id
    )
    
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    
    # Send emails asynchronously (in background)
    # Note: For production, use Celery or background tasks
    try:
        send_inquiry_admin_notification(
            inquiry_id=inquiry.id,
            name=name,
            email=email,
            phone=phone,
            message=message,
            property_title=property_title
        )
        
        send_inquiry_user_acknowledgement(
            name=name,
            email=email,
            property_title=property_title
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Email sending failed: {e}")
    
    return {
        "success": True,
        "message": "Thank you for your interest! We will contact you soon.",
        "inquiry_id": inquiry.id
    }
