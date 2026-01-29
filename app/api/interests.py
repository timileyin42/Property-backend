from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import require_admin
from app.models.user import User
from app.models.inquiry import PropertyInquiry, InquiryStatus
from app.schemas.inquiry import InquiryResponse, InquiryUpdate, InquiryListResponse
from datetime import datetime, timezone

router = APIRouter(prefix="/api/admin/interests", tags=["Admin - Interests"], dependencies=[Depends(require_admin)])


@router.get("", response_model=InquiryListResponse)
def get_all_interests(
    status_filter: InquiryStatus = Query(None),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get all property interests (Authenticated Users) (Admin only)
    
    Filter by status and paginate results.
    """
    # Filter for authenticated users (user_id IS NOT NULL)
    query = db.query(PropertyInquiry).filter(PropertyInquiry.user_id.isnot(None))
    
    # Filter by status if specified
    if status_filter:
        query = query.filter(PropertyInquiry.status == status_filter)
    
    # Get total count
    total = query.count()
    
    # Get counts by status (scoped to authenticated users)
    base_count_query = db.query(PropertyInquiry).filter(PropertyInquiry.user_id.isnot(None))
    new_count = base_count_query.filter(PropertyInquiry.status == InquiryStatus.NEW).count()
    contacted_count = base_count_query.filter(PropertyInquiry.status == InquiryStatus.CONTACTED).count()
    closed_count = base_count_query.filter(PropertyInquiry.status == InquiryStatus.CLOSED).count()
    
    # Get interests
    interests = query.order_by(PropertyInquiry.created_at.desc()).offset(skip).limit(limit).all()
    
    # Enrich with property and admin info
    for interest in interests:
        if interest.property:
            interest.property_title = interest.property.title
        if interest.assigned_admin:
            interest.assigned_admin_name = interest.assigned_admin.full_name
    
    return InquiryListResponse(
        inquiries=interests,
        total=total,
        new_count=new_count,
        contacted_count=contacted_count,
        closed_count=closed_count
    )


@router.get("/{interest_id}", response_model=InquiryResponse)
def get_interest(
    interest_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get specific interest details (Admin only)
    """
    interest = db.query(PropertyInquiry).filter(
        PropertyInquiry.id == interest_id,
        PropertyInquiry.user_id.isnot(None)
    ).first()
    
    if not interest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interest not found"
        )
    
    # Enrich with property and admin info
    if interest.property:
        interest.property_title = interest.property.title
    if interest.assigned_admin:
        interest.assigned_admin_name = interest.assigned_admin.full_name
    
    return interest


@router.patch("/{interest_id}", response_model=InquiryResponse)
def update_interest(
    interest_id: int,
    inquiry_update: InquiryUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update interest status and details (Admin only)
    """
    interest = db.query(PropertyInquiry).filter(
        PropertyInquiry.id == interest_id,
        PropertyInquiry.user_id.isnot(None)
    ).first()
    
    if not interest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interest not found"
        )
    
    # Update fields
    update_data = inquiry_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(interest, field, value)
    
    # Set contacted_at if status changed to CONTACTED
    if inquiry_update.status == InquiryStatus.CONTACTED and not interest.contacted_at:
        interest.contacted_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(interest)
    
    # Enrich response
    if interest.property:
        interest.property_title = interest.property.title
    if interest.assigned_admin:
        interest.assigned_admin_name = interest.assigned_admin.full_name
    
    return interest


@router.delete("/{interest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interest(
    interest_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete an interest (Admin only)
    """
    interest = db.query(PropertyInquiry).filter(
        PropertyInquiry.id == interest_id,
        PropertyInquiry.user_id.isnot(None)
    ).first()
    
    if not interest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interest not found"
        )
    
    db.delete(interest)
    db.commit()
    
    return None
