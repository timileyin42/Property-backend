from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import require_admin
from app.models.user import User
from app.models.inquiry import PropertyInquiry, InquiryStatus
from app.models.property import Property
from app.schemas.inquiry import InquiryResponse, InquiryUpdate, InquiryListResponse
from datetime import datetime

router = APIRouter(prefix="/api/admin/inquiries", tags=["Admin - Inquiries"], dependencies=[Depends(require_admin)])


@router.get("", response_model=InquiryListResponse)
def get_all_inquiries(
    status_filter: InquiryStatus = Query(None),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get all property inquiries (Admin only)
    
    Filter by status and paginate results.
    """
    query = db.query(PropertyInquiry)
    
    # Filter by status if specified
    if status_filter:
        query = query.filter(PropertyInquiry.status == status_filter)
    
    # Get total count
    total = query.count()
    
    # Get counts by status
    new_count = db.query(PropertyInquiry).filter(PropertyInquiry.status == InquiryStatus.NEW).count()
    contacted_count = db.query(PropertyInquiry).filter(PropertyInquiry.status == InquiryStatus.CONTACTED).count()
    closed_count = db.query(PropertyInquiry).filter(PropertyInquiry.status == InquiryStatus.CLOSED).count()
    
    # Get inquiries
    inquiries = query.order_by(PropertyInquiry.created_at.desc()).offset(skip).limit(limit).all()
    
    # Enrich with property and admin info
    for inquiry in inquiries:
        if inquiry.property:
            inquiry.property_title = inquiry.property.title
        if inquiry.assigned_admin:
            inquiry.assigned_admin_name = inquiry.assigned_admin.full_name
    
    return InquiryListResponse(
        inquiries=inquiries,
        total=total,
        new_count=new_count,
        contacted_count=contacted_count,
        closed_count=closed_count
    )


@router.get("/{inquiry_id}", response_model=InquiryResponse)
def get_inquiry(
    inquiry_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get specific inquiry details (Admin only)
    """
    inquiry = db.query(PropertyInquiry).filter(PropertyInquiry.id == inquiry_id).first()
    
    if not inquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inquiry not found"
        )
    
    # Enrich with property and admin info
    if inquiry.property:
        inquiry.property_title = inquiry.property.title
    if inquiry.assigned_admin:
        inquiry.assigned_admin_name = inquiry.assigned_admin.full_name
    
    return inquiry


@router.patch("/{inquiry_id}", response_model=InquiryResponse)
def update_inquiry(
    inquiry_id: int,
    inquiry_update: InquiryUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update inquiry status and details (Admin only)
    """
    inquiry = db.query(PropertyInquiry).filter(PropertyInquiry.id == inquiry_id).first()
    
    if not inquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inquiry not found"
        )
    
    # Update fields
    update_data = inquiry_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(inquiry, field, value)
    
    # Set contacted_at if status changed to CONTACTED
    if inquiry_update.status == InquiryStatus.CONTACTED and not inquiry.contacted_at:
        inquiry.contacted_at = datetime.utcnow()
    
    db.commit()
    db.refresh(inquiry)
    
    # Enrich response
    if inquiry.property:
        inquiry.property_title = inquiry.property.title
    if inquiry.assigned_admin:
        inquiry.assigned_admin_name = inquiry.assigned_admin.full_name
    
    return inquiry


@router.delete("/{inquiry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inquiry(
    inquiry_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete an inquiry (Admin only)
    """
    inquiry = db.query(PropertyInquiry).filter(PropertyInquiry.id == inquiry_id).first()
    
    if not inquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inquiry not found"
        )
    
    db.delete(inquiry)
    db.commit()
    
    return None
