from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User, UserRole
from app.models.property import Property
from app.models.inquiry import PropertyInquiry, InquiryStatus
from app.models.wishlist import Wishlist
from app.models.investment_application import InvestmentApplication, ApplicationStatus
from app.models.update import Update, UpdateComment, UpdateLike
from app.models.investment import Investment
from app.schemas.user import ProfileUpdate, UserResponse
from app.schemas.inquiry import InquiryResponse, InquiryListResponse
from app.schemas.wishlist import WishlistCreate, WishlistUpdate, WishlistResponse, WishlistListResponse
from app.schemas.investment_application import InvestmentApplicationCreate, InvestmentApplicationUpdate, InvestmentApplicationResponse
from app.schemas.update import UpdateCommentCreate, UpdateCommentResponse, CommentListResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["User Dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/profile", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's profile information
    """
    return current_user


@router.patch("/profile", response_model=UserResponse)
def update_my_profile(
    profile_update: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information
    """
    update_data = profile_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.get("/interests", response_model=InquiryListResponse)
def get_my_interests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all interests submitted by the current user
    
    Shows history and status updates
    """
    inquiries = db.query(PropertyInquiry).filter(
        PropertyInquiry.user_id == current_user.id
    ).order_by(PropertyInquiry.created_at.desc()).all()
    
    # Enrich with property info
    for inquiry in inquiries:
        if inquiry.property:
            inquiry.property_title = inquiry.property.title
        if inquiry.assigned_admin:
            inquiry.assigned_admin_name = inquiry.assigned_admin.full_name
    
    # Get status counts
    total = len(inquiries)
    new_count = sum(1 for i in inquiries if i.status == InquiryStatus.NEW)
    contacted_count = sum(1 for i in inquiries if i.status == InquiryStatus.CONTACTED)
    closed_count = sum(1 for i in inquiries if i.status == InquiryStatus.CLOSED)
    
    return InquiryListResponse(
        inquiries=inquiries,
        total=total,
        new_count=new_count,
        contacted_count=contacted_count,
        closed_count=closed_count
    )


@router.post("/interests", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def submit_interest(
    property_id: int = Body(...),
    message: str = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Express interest in a property (Authenticated User)
    
    Automatically links to user account and uses profile information
    """
    from app.services.email_service import (
        send_inquiry_admin_notification,
        send_inquiry_user_acknowledgement
    )
    
    # Verify property exists
    property = db.query(Property).filter(Property.id == property_id).first()
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Create inquiry
    safe_name = current_user.full_name or (current_user.email or "User")
    safe_email = current_user.email or "no-reply@example.com"
    safe_phone = current_user.phone or "Not provided"
    inquiry = PropertyInquiry(
        user_id=current_user.id,
        name=safe_name,
        email=safe_email,
        phone=safe_phone,
        message=message,
        property_id=property_id
    )
    
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    
    # Send email notifications
    try:
        send_inquiry_admin_notification(
            inquiry_id=inquiry.id,
            name=safe_name,
            email=safe_email,
            phone=safe_phone,
            message=message,
            property_title=property.title
        )
        
        send_inquiry_user_acknowledgement(
            name=safe_name,
            email=safe_email,
            property_title=property.title
        )
    except Exception as e:
        print(f"Email sending failed: {e}")
    
    # Enrich response
    inquiry.property_title = property.title
    
    return inquiry


@router.get("/wishlist", response_model=WishlistListResponse)
def get_my_wishlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's wishlist/saved properties
    """
    wishlist_items = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id
    ).order_by(Wishlist.created_at.desc()).all()
    
    # Enrich with property details
    enriched_items = []
    for item in wishlist_items:
        property = db.query(Property).filter(Property.id == item.property_id).first()
        if property:
            item.property_title = property.title
            item.property_location = property.location
            item.property_status = property.status.value
            item.property_image = property.image_urls[0] if property.image_urls else None
            item.property_video = property.video_urls[0] if property.video_urls else None
        enriched_items.append(item)
    
    return WishlistListResponse(
        items=enriched_items,
        total=len(enriched_items)
    )


@router.post("/wishlist", response_model=WishlistResponse, status_code=status.HTTP_201_CREATED)
def add_to_wishlist(
    wishlist_create: WishlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a property to wishlist
    """
    # Verify property exists
    property = db.query(Property).filter(Property.id == wishlist_create.property_id).first()
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Check if already in wishlist
    existing = db.query(Wishlist).filter(
        Wishlist.user_id == current_user.id,
        Wishlist.property_id == wishlist_create.property_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Property already in wishlist"
        )
    
    # Create wishlist item
    wishlist_item = Wishlist(
        user_id=current_user.id,
        property_id=wishlist_create.property_id,
        notify_on_update=wishlist_create.notify_on_update,
        notify_on_price_change=wishlist_create.notify_on_price_change
    )
    
    db.add(wishlist_item)
    db.commit()
    db.refresh(wishlist_item)
    
    # Enrich response
    wishlist_item.property_title = property.title
    wishlist_item.property_location = property.location
    wishlist_item.property_status = property.status.value
    wishlist_item.property_image = property.image_urls[0] if property.image_urls else None
    wishlist_item.property_video = property.video_urls[0] if property.video_urls else None
    
    return wishlist_item


@router.patch("/wishlist/{wishlist_id}", response_model=WishlistResponse)
def update_wishlist_item(
    wishlist_id: int,
    wishlist_update: WishlistUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update wishlist notification preferences
    """
    wishlist_item = db.query(Wishlist).filter(
        Wishlist.id == wishlist_id,
        Wishlist.user_id == current_user.id
    ).first()
    
    if not wishlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found"
        )
    
    if wishlist_update.notify_on_update is not None:
        wishlist_item.notify_on_update = wishlist_update.notify_on_update
    
    if wishlist_update.notify_on_price_change is not None:
        wishlist_item.notify_on_price_change = wishlist_update.notify_on_price_change
    
    db.commit()
    db.refresh(wishlist_item)
    
    return wishlist_item


@router.delete("/wishlist/{wishlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_wishlist(
    wishlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a property from wishlist
    """
    wishlist_item = db.query(Wishlist).filter(
        Wishlist.id == wishlist_id,
        Wishlist.user_id == current_user.id
    ).first()
    
    if not wishlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist item not found"
        )
    
    db.delete(wishlist_item)
    db.commit()
    
    return None


@router.post("/investment-applications", response_model=InvestmentApplicationResponse, status_code=status.HTTP_201_CREATED)
def submit_investment_application(
    application_data: InvestmentApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit an application to become an investor
    
    Applications are auto-approved and users are upgraded immediately.
    """
    from app.services.email_service import send_application_approved
    
    existing_application = db.query(InvestmentApplication).filter(
        InvestmentApplication.user_id == current_user.id
    ).order_by(InvestmentApplication.created_at.desc()).first()
    
    if existing_application:
        if existing_application.status != ApplicationStatus.APPROVED:
            existing_application.status = ApplicationStatus.APPROVED
            existing_application.reviewed_at = datetime.now(timezone.utc)
            existing_application.admin_notes = "Auto-approved"
            db.commit()
            db.refresh(existing_application)
        if current_user.role != UserRole.INVESTOR:
            current_user.role = UserRole.INVESTOR
            db.commit()
            db.refresh(current_user)
        return existing_application
    
    # Create new application
    new_application = InvestmentApplication(
        user_id=current_user.id,
        status=ApplicationStatus.APPROVED,
        reviewed_at=datetime.now(timezone.utc),
        admin_notes="Auto-approved",
        **application_data.model_dump()
    )
    
    db.add(new_application)
    current_user.role = UserRole.INVESTOR
    db.commit()
    db.refresh(new_application)

    try:
        send_application_approved(
            email=current_user.email,
            name=current_user.full_name,
            admin_notes="Auto-approved"
        )
    except Exception as e:
        logger.error(f"Failed to send auto-approval email for application {new_application.id}: {e}")
    
    return new_application


@router.get("/investment-applications", response_model=list[InvestmentApplicationResponse])
def get_my_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all investment applications submitted by current user
    """
    applications = db.query(InvestmentApplication).filter(
        InvestmentApplication.user_id == current_user.id
    ).order_by(InvestmentApplication.created_at.desc()).all()
    
    # Enrich with reviewer name if available
    for app in applications:
        if app.reviewer:
            app.reviewer_name = app.reviewer.full_name
    
    return applications


@router.patch("/investment-applications/{application_id}", response_model=InvestmentApplicationResponse)
def update_my_application(
    application_id: int,
    application_update: InvestmentApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update investment application (only if still pending)
    """
    application = db.query(InvestmentApplication).filter(
        InvestmentApplication.id == application_id,
        InvestmentApplication.user_id == current_user.id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    if application.status != ApplicationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update application that has been reviewed"
        )
    
    # Update fields
    if application_update.motivation is not None:
        application.motivation = application_update.motivation
    
    if application_update.investment_amount is not None:
        application.investment_amount = application_update.investment_amount
    
    if application_update.experience is not None:
        application.experience = application_update.experience
    
    db.commit()
    db.refresh(application)
    
    return application


@router.post("/updates/{update_id}/comments", response_model=UpdateCommentResponse, status_code=status.HTTP_201_CREATED)
def create_update_comment(
    update_id: int,
    comment_data: UpdateCommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a comment to an update
    """
    # Verify update exists
    update = db.query(Update).filter(Update.id == update_id).first()
    if not update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Update not found"
        )

    if update.off_plan_only:
        invested = db.query(Investment).filter(
            Investment.user_id == current_user.id,
            Investment.property_id == update.property_id
        ).first()
        if not invested:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This update is available to investors only"
            )
    
    # Create comment
    comment = UpdateComment(
        update_id=update_id,
        user_id=current_user.id,
        content=comment_data.content
    )
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    # Enrich response
    comment.user_name = current_user.full_name or "User"
    comment.user_avatar = None  # Placeholder
    
    return comment


@router.get("/updates/{update_id}/comments", response_model=CommentListResponse)
def get_update_comments(
    update_id: int,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comments for an update
    """
    # Verify update exists
    update = db.query(Update).filter(Update.id == update_id).first()
    if not update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Update not found"
        )

    if update.off_plan_only:
        invested = db.query(Investment).filter(
            Investment.user_id == current_user.id,
            Investment.property_id == update.property_id
        ).first()
        if not invested:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This update is available to investors only"
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


@router.delete("/updates/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_update_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a comment (User can only delete their own)
    """
    comment = db.query(UpdateComment).filter(
        UpdateComment.id == comment_id,
        UpdateComment.user_id == current_user.id
    ).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found or not owned by user"
        )
    
    db.delete(comment)
    db.commit()
    
    return None


@router.post("/updates/{update_id}/like", status_code=status.HTTP_200_OK)
def toggle_update_like(
    update_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toggle like on an update
    Returns {"liked": bool}
    """
    # Verify update exists
    update = db.query(Update).filter(Update.id == update_id).first()
    if not update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Update not found"
        )

    if update.off_plan_only:
        invested = db.query(Investment).filter(
            Investment.user_id == current_user.id,
            Investment.property_id == update.property_id
        ).first()
        if not invested:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This update is available to investors only"
            )
    
    # Check if already liked
    existing_like = db.query(UpdateLike).filter(
        UpdateLike.update_id == update_id,
        UpdateLike.user_id == current_user.id
    ).first()
    
    if existing_like:
        # Unlike
        db.delete(existing_like)
        db.commit()
        return {"liked": False}
    else:
        # Like
        new_like = UpdateLike(
            update_id=update_id,
            user_id=current_user.id
        )
        db.add(new_like)
        db.commit()
        return {"liked": True}
