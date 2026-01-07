from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import require_admin
from app.models.user import User, UserRole
from app.models.property import Property
from app.models.investment import Investment
from app.models.update import Update
from app.models.investment_application import InvestmentApplication, ApplicationStatus
from app.schemas.user import UserListResponse, UserRoleUpdate, UserResponse
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyResponse
from app.schemas.investment import InvestmentCreate, InvestmentUpdate, InvestmentResponse
from app.schemas.update import UpdateCreate, UpdateResponse
from app.schemas.investment_application import InvestmentApplicationResponse, InvestmentApplicationReview
from sqlalchemy.sql import func

router = APIRouter(prefix="/api/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=UserListResponse)
def get_all_users(
    page: int = 1,
    page_size: int = 10,
    role: UserRole = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get list of all users (admin only)
    
    Supports filtering by role and pagination.
    """
    query = db.query(User)
    
    # Filter by role if provided
    if role:
        query = query.filter(User.role == role)
    
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
    """
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
    
    new_update = Update(**update_data.model_dump())
    
    db.add(new_update)
    db.commit()
    db.refresh(new_update)
    
    return new_update


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
