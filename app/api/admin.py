from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import require_admin
from app.models.user import User, UserRole
from app.models.property import Property
from app.models.investment import Investment
from app.models.update import Update, UpdateComment, UpdateLike, UpdateMedia
from app.models.investment_application import InvestmentApplication, ApplicationStatus
from app.models.inquiry import PropertyInquiry
from app.schemas.user import UserListResponse, UserRoleUpdate, UserResponse, UserAdminUpdate
from app.schemas.common import BulkDeleteRequest, BulkDeleteResponse
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyResponse, PropertyListResponse
from app.schemas.investment import (
    InvestmentCreate,
    InvestmentUpdate,
    InvestmentResponse,
    InvestmentListResponse,
)
from app.schemas.update import UpdateCreate, UpdateUpdate, UpdateResponse, CommentListResponse, UpdateDetailResponse
from app.schemas.investment_application import InvestmentApplicationResponse, InvestmentApplicationReview
from app.schemas.dashboard import DashboardStatsResponse
from sqlalchemy.sql import func
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/api/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


@router.get("/dashboard-stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get summary statistics for admin dashboard
    """
    # Time deltas
    now = datetime.now(timezone.utc)
    one_week_ago = now - timedelta(days=7)
    one_month_ago = now - timedelta(days=30)
    
    # 1. Total Interests (Investment Applications + Property Inquiries)
    # Count Investment Applications
    total_applications = db.query(InvestmentApplication).count()
    applications_this_week = db.query(InvestmentApplication).filter(InvestmentApplication.created_at >= one_week_ago).count()
    
    # Count Property Inquiries
    total_inquiries = db.query(PropertyInquiry).count()
    inquiries_this_week = db.query(PropertyInquiry).filter(PropertyInquiry.created_at >= one_week_ago).count()
    
    # Combine
    total_interests = total_applications + total_inquiries
    interests_this_week = applications_this_week + inquiries_this_week
    
    # 2. Active Properties
    active_properties = db.query(Property).count()
    fully_subscribed = db.query(Property).filter(Property.fractions_sold >= Property.total_fractions).count()
    
    # 3. Total Users
    total_users = db.query(User).count()
    users_this_month = db.query(User).filter(User.created_at >= one_month_ago).count()
    
    # 4. Total Investment (capital invested, not valuation)
    total_investment = db.query(func.sum(Investment.initial_value)).scalar() or 0.0
    investment_this_month = db.query(func.sum(Investment.initial_value)).filter(Investment.created_at >= one_month_ago).scalar() or 0.0
    
    # Growth based on new invested capital this month
    investment_growth_pct = 0.0
    if total_investment > 0:
        investment_growth_pct = (investment_this_month / total_investment) * 100
    
    return DashboardStatsResponse(
        total_interests=total_interests,
        active_properties=active_properties,
        total_users=total_users,
        total_investment=total_investment,
        interests_growth=f"+{interests_this_week} this week",
        properties_growth=f"{fully_subscribed} fully subscribed",
        users_growth=f"+{users_this_month} this month",
        investment_growth=f"+{round(investment_growth_pct, 1)}% this month"
    )


@router.get("/investments", response_model=InvestmentListResponse)
def list_investments(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all investments with property info (admin only)."""
    query = db.query(Investment)
    total = query.count()
    skip = (page - 1) * page_size
    investments = query.order_by(Investment.created_at.desc()).offset(skip).limit(page_size).all()

    responses: list[InvestmentResponse] = []
    for inv in investments:
        prop = db.query(Property).filter(Property.id == inv.property_id).first()
        responses.append(
            InvestmentResponse(
                id=inv.id,
                user_id=inv.user_id,
                property_id=inv.property_id,
                fractions_owned=inv.fractions_owned,
                ownership_percentage=inv.ownership_percentage,
                initial_value=inv.initial_value,
                current_value=inv.current_value,
                growth_percentage=inv.growth_percentage,
                growth_amount=inv.growth_amount,
                created_at=inv.created_at,
                updated_at=inv.updated_at,
                property_title=prop.title if prop else None,
                property_location=prop.location if prop else None,
            )
        )

    # Aggregate totals
    total_initial = sum(inv.initial_value for inv in investments)
    total_current = sum(inv.current_value for inv in investments)
    total_growth_pct = (
        ((total_current - total_initial) / total_initial * 100) if total_initial > 0 else 0
    )

    return InvestmentListResponse(
        investments=responses,
        total=total,
        total_initial_value=total_initial,
        total_current_value=total_current,
        total_growth_percentage=total_growth_pct,
    )


@router.get("/users", response_model=UserListResponse)
def get_all_users(
    page: int = 1,
    page_size: int = 10,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get list of all users (admin only)
    
    Supports filtering by role and pagination.
    """
    query = db.query(User)
    
    # Filter by role if provided (case-insensitive)
    if role:
        try:
            normalized_role = UserRole(role.strip().upper())
        except ValueError as exc:
            valid_roles = ", ".join([r.value for r in UserRole])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Valid roles: {valid_roles}"
            ) from exc
        query = query.filter(User.role == normalized_role)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    skip = (page - 1) * page_size
    users = query.order_by(User.created_at.desc()).offset(skip).limit(page_size).all()
    
    return UserListResponse(
        users=users,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_details(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get specific user details (admin only)
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user_details(
    user_id: int,
    user_update: UserAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update user details (admin only)
    
    Can update name, phone, email, and active status.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete a user (admin only)
    
    Warning: This will cascade delete their investments, inquiries, etc.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    db.delete(user)
    db.commit()
    
    return None


@router.delete("/users", response_model=BulkDeleteResponse)
def bulk_delete_users(
    payload: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Bulk delete users (admin only)
    """
    ids = list(dict.fromkeys(payload.ids))
    if not ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user ids provided"
        )

    if current_user.id in ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )

    existing_rows = db.query(User.id).filter(User.id.in_(ids)).all()
    existing_ids = [row[0] for row in existing_rows]
    missing_ids = [user_id for user_id in ids if user_id not in existing_ids]

    if existing_ids:
        db.query(User).filter(User.id.in_(existing_ids)).delete(synchronize_session=False)
        db.commit()

    return BulkDeleteResponse(deleted_count=len(existing_ids), missing_ids=missing_ids)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update user role (admin only)
    
    This is how admins promote users to INVESTOR status.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update role
    user.role = role_update.role
    db.commit()
    db.refresh(user)
    
    return user



@router.get("/properties", response_model=PropertyListResponse)
def list_properties(
    page: int = 1,
    page_size: int = 20,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List all properties with pagination (admin only)
    
    Can optionally filter by status (AVAILABLE, SOLD, etc.)
    """
    from app.schemas.property import PropertyListResponse
    
    query = db.query(Property)
    
    # Optional status filter
    if status:
        query = query.filter(Property.status == status)
        
    total = query.count()
    skip = (page - 1) * page_size
    properties = query.order_by(Property.created_at.desc()).offset(skip).limit(page_size).all()
    
    return PropertyListResponse(
        properties=properties,
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/properties", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
def create_property(
    property_data: PropertyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Create a new property (admin only)
    """
    new_property = Property(**property_data.model_dump())
    
    db.add(new_property)
    db.commit()
    db.refresh(new_property)
    
    return new_property


@router.patch("/properties/{property_id}", response_model=PropertyResponse)
def update_property(
    property_id: int,
    property_data: PropertyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update property information (admin only)
    """
    property = db.query(Property).filter(Property.id == property_id).first()
    
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Update fields
    update_data = property_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(property, field, value)
    
    db.commit()
    db.refresh(property)
    
    return property


@router.delete("/properties/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete a property (admin only)
    """
    property = db.query(Property).filter(Property.id == property_id).first()
    
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    db.delete(property)
    db.commit()
    
    return None


@router.delete("/properties", response_model=BulkDeleteResponse)
def bulk_delete_properties(
    payload: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Bulk delete properties (admin only)
    """
    ids = list(dict.fromkeys(payload.ids))
    if not ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No property ids provided"
        )

    existing_rows = db.query(Property.id).filter(Property.id.in_(ids)).all()
    existing_ids = [row[0] for row in existing_rows]
    missing_ids = [property_id for property_id in ids if property_id not in existing_ids]

    if existing_ids:
        db.query(Property).filter(Property.id.in_(existing_ids)).delete(synchronize_session=False)
        db.commit()

    return BulkDeleteResponse(deleted_count=len(existing_ids), missing_ids=missing_ids)


@router.post("/investments", response_model=InvestmentResponse, status_code=status.HTTP_201_CREATED)
def assign_investment(
    investment_data: InvestmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Assign an investment to a user (admin only)
    
    This is the core of the business model - admins manually assign
    investments after offline verification and agreement.
    """
    # Verify user exists and is an investor
    user = db.query(User).filter(User.id == investment_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.role not in [UserRole.INVESTOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be an INVESTOR to receive investments"
        )
    
    # Verify property exists
    property = db.query(Property).filter(Property.id == investment_data.property_id).first()
    if not property:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Create investment
    new_investment = Investment(**investment_data.model_dump())
    
    db.add(new_investment)
    db.commit()
    db.refresh(new_investment)
    
    return new_investment


@router.patch("/investments/{investment_id}/valuation", response_model=InvestmentResponse)
def update_investment_valuation(
    investment_id: int,
    valuation_update: InvestmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update investment current valuation (admin only)
    
    Admins manually update valuations based on real market data.
    Creates a portfolio snapshot to track historical growth.
    """
    from app.services.portfolio_service import create_portfolio_snapshot
    
    investment = db.query(Investment).filter(Investment.id == investment_id).first()
    
    if not investment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investment not found"
        )
    
    # Update current value
    investment.current_value = valuation_update.current_value
    db.commit()
    db.refresh(investment)
    
    # Create/update snapshot to track this valuation change
    # force_update=True ensures today's snapshot reflects the latest values
    try:
        create_portfolio_snapshot(investment.user_id, db, force_update=True)
    except Exception as e:
        # Log but don't fail the request
        import logging
        logging.error(f"Failed to create portfolio snapshot: {e}")
    
    return investment


@router.post("/updates", response_model=UpdateResponse, status_code=status.HTTP_201_CREATED)
def create_update(
    update_data: UpdateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Post a property update/news (admin only)
    """
    # Verify property exists if property_id is provided
    if update_data.property_id:
        property = db.query(Property).filter(Property.id == update_data.property_id).first()
        if not property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
    
    # Extract media_files if present
    update_dict = update_data.model_dump()
    media_files_list = update_dict.pop('media_files', None)
    
    new_update = Update(**update_dict)
    
    db.add(new_update)
    db.flush()  # Generate ID
    
    # Add media files if provided
    if media_files_list:
        for media in media_files_list:
            new_media = UpdateMedia(
                update_id=new_update.id,
                media_type=media['media_type'],
                url=media['url']
            )
            db.add(new_media)
    
    db.commit()
    db.refresh(new_update)
    
    return new_update


@router.patch("/updates/{update_id}", response_model=UpdateResponse)
def update_update_news(
    update_id: int,
    update_data: UpdateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update a property update/news (admin only)
    """
    update_item = db.query(Update).filter(Update.id == update_id).first()
    
    if not update_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Update not found"
        )
        
    # Verify property exists if property_id is provided
    if update_data.property_id is not None:
        property = db.query(Property).filter(Property.id == update_data.property_id).first()
        if not property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
    
    # Update fields
    data = update_data.model_dump(exclude_unset=True)
    media_files_list = data.pop('media_files', None)
    
    for field, value in data.items():
        setattr(update_item, field, value)
    
    # Update media files if provided
    if media_files_list is not None:
        # Remove existing media
        db.query(UpdateMedia).filter(UpdateMedia.update_id == update_id).delete()
        
        # Add new media
        for media in media_files_list:
            new_media = UpdateMedia(
                update_id=update_id,
                media_type=media['media_type'],
                url=media['url']
            )
            db.add(new_media)
    
    db.commit()
    db.refresh(update_item)
    
    return update_item


@router.get("/updates/{update_id}", response_model=UpdateDetailResponse)
def get_update_details(
    update_id: int,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get update details with comments (Admin View)
    """
    update = db.query(Update).filter(Update.id == update_id).first()
    if not update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Update not found"
        )

    if update.property_id:
        property = db.query(Property).filter(Property.id == update.property_id).first()
        if property:
            update.property_title = property.title

    update.likes_count = db.query(UpdateLike).filter(UpdateLike.update_id == update.id).count()
    update.comments_count = db.query(UpdateComment).filter(UpdateComment.update_id == update.id).count()
    update.is_liked_by_user = False

    query = db.query(UpdateComment).filter(UpdateComment.update_id == update_id)
    total = query.count()
    skip = (page - 1) * page_size
    comments = query.order_by(UpdateComment.created_at.desc()).offset(skip).limit(page_size).all()

    for comment in comments:
        if comment.user:
            comment.user_name = comment.user.full_name or "User"

    return UpdateDetailResponse(
        update=update,
        comments=CommentListResponse(
            comments=comments,
            total=total,
            page=page,
            page_size=page_size
        )
    )


@router.get("/updates/{update_id}/comments", response_model=CommentListResponse)
def get_update_comments(
    update_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get all comments for an update (Admin View)
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


@router.delete("/updates/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete any comment (Admin only)
    """
    comment = db.query(UpdateComment).filter(UpdateComment.id == comment_id).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    db.delete(comment)
    db.commit()
    
    return None


@router.delete("/updates/comments", response_model=BulkDeleteResponse)
def bulk_delete_comments(
    payload: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Bulk delete update comments (admin only)
    """
    ids = list(dict.fromkeys(payload.ids))
    if not ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No comment ids provided"
        )

    existing_rows = db.query(UpdateComment.id).filter(UpdateComment.id.in_(ids)).all()
    existing_ids = [row[0] for row in existing_rows]
    missing_ids = [comment_id for comment_id in ids if comment_id not in existing_ids]

    if existing_ids:
        db.query(UpdateComment).filter(UpdateComment.id.in_(existing_ids)).delete(synchronize_session=False)
        db.commit()

    return BulkDeleteResponse(deleted_count=len(existing_ids), missing_ids=missing_ids)


@router.get("/investment-applications", response_model=list[InvestmentApplicationResponse])
def get_all_applications(
    status: ApplicationStatus = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get all investment applications (admin only)
    
    Can filter by status (PENDING, UNDER_REVIEW, APPROVED, REJECTED)
    """
    query = db.query(InvestmentApplication)
    
    if status:
        query = query.filter(InvestmentApplication.status == status)
    
    applications = query.order_by(InvestmentApplication.created_at.desc()).all()
    
    # Enrich with user and reviewer info
    for app in applications:
        app.user_name = app.user.full_name
        app.user_email = app.user.email
        if app.reviewer:
            app.reviewer_name = app.reviewer.full_name
    
    return applications


@router.patch("/investment-applications/{application_id}", response_model=InvestmentApplicationResponse)
def review_application(
    application_id: int,
    review_data: InvestmentApplicationReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Review an investment application (admin only)
    
    Approve or reject applications. If approved, user's role is upgraded to INVESTOR.
    """
    from app.services.email_service import send_application_approved, send_application_rejected
    import logging
    
    logger = logging.getLogger(__name__)
    
    application = db.query(InvestmentApplication).filter(
        InvestmentApplication.id == application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Get user for email notification
    user = db.query(User).filter(User.id == application.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update application status
    application.status = review_data.status
    application.reviewed_by = current_user.id
    application.reviewed_at = func.now()
    application.admin_notes = review_data.admin_notes
    application.rejection_reason = review_data.rejection_reason
    
    # If approved, upgrade user role to INVESTOR
    if review_data.status == ApplicationStatus.APPROVED:
        user.role = UserRole.INVESTOR
        
        # Send approval email
        try:
            send_application_approved(
                email=user.email,
                name=user.full_name,
                admin_notes=review_data.admin_notes
            )
        except Exception as e:
            logger.error(f"Failed to send approval email to {user.email}: {e}")
    
    # If rejected, send rejection email
    elif review_data.status == ApplicationStatus.REJECTED:
        try:
            send_application_rejected(
                email=user.email,
                name=user.full_name,
                rejection_reason=review_data.rejection_reason
            )
        except Exception as e:
            logger.error(f"Failed to send rejection email to {user.email}: {e}")
    
    db.commit()
    db.refresh(application)
    
    # Enrich response
    application.user_name = application.user.full_name
    application.user_email = application.user.email
    application.reviewer_name = current_user.full_name
    
    return application
