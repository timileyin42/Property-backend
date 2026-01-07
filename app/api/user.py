from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User
from app.models.property import Property
from app.models.inquiry import PropertyInquiry, InquiryStatus
from app.models.wishlist import Wishlist
from app.models.investment_application import InvestmentApplication, ApplicationStatus
from app.schemas.user import ProfileUpdate, UserResponse
from app.schemas.inquiry import InquiryResponse, InquiryListResponse
from app.schemas.wishlist import WishlistCreate, WishlistUpdate, WishlistResponse, WishlistListResponse
from app.schemas.investment_application import InvestmentApplicationCreate, InvestmentApplicationUpdate, InvestmentApplicationResponse
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
    if profile_update.full_name is not None:
        current_user.full_name = profile_update.full_name
    
    if profile_update.phone is not None:
        current_user.phone = profile_update.phone
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.get("/inquiries", response_model=InquiryListResponse)
def get_my_inquiries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all inquiries submitted by the current user
    
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


@router.post("/inquiries", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def submit_authenticated_inquiry(
    property_id: int = Body(...),
    message: str = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit an inquiry as authenticated user
    
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
    inquiry = PropertyInquiry(
        user_id=current_user.id,
        name=current_user.full_name,
        email=current_user.email,
        phone=current_user.phone or "Not provided",
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
            name=current_user.full_name,
            email=current_user.email,
            phone=current_user.phone or "Not provided",
            message=message,
            property_title=property.title
        )
        
        send_inquiry_user_acknowledgement(
            name=current_user.full_name,
            email=current_user.email,
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
    
    Users can apply to upgrade their role to INVESTOR.
    Admins will review and approve/reject applications.
    """
    from app.services.email_service import send_application_admin_notification
    
    # Check if user already has a pending application
    existing_application = db.query(InvestmentApplication).filter(
        InvestmentApplication.user_id == current_user.id,
        InvestmentApplication.status == ApplicationStatus.PENDING
    ).first()
    
    if existing_application:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pending application"
        )
    
    # Create new application
    new_application = InvestmentApplication(
        user_id=current_user.id,
        **application_data.model_dump()
    )
    
    db.add(new_application)
    db.commit()
    db.refresh(new_application)
    
    # Send email notification to admin
    try:
        send_application_admin_notification(
            application_id=new_application.id,
            user_name=current_user.full_name,
            user_email=current_user.email,
            motivation=application_data.motivation,
            investment_amount=application_data.investment_amount,
            experience=application_data.experience
        )
    except Exception as e:
        # Log error but don't fail the request
        logger.error(f"Failed to send admin notification for application {new_application.id}: {e}")
    
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
