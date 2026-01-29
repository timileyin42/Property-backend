from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.inquiry import PropertyInquiry
from app.schemas.inquiry import InquiryCreate, InquiryResponse
from app.services.email_service import (
    send_inquiry_admin_notification,
    send_inquiry_user_acknowledgement
)

router = APIRouter(prefix="/api/contact", tags=["Public - Contact"])


@router.post("", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def submit_inquiry(
    inquiry_data: InquiryCreate,
    db: Session = Depends(get_db)
):
    """
    Submit a general inquiry or express interest in a property (Unauthenticated)
    """
    # Create new inquiry
    new_inquiry = PropertyInquiry(
        name=inquiry_data.name,
        email=inquiry_data.email,
        phone=inquiry_data.phone,
        message=inquiry_data.message,
        property_id=inquiry_data.property_id,
        user_id=None  # Explicitly set to None for unauthenticated users
    )
    
    db.add(new_inquiry)
    db.commit()
    db.refresh(new_inquiry)
    
    # Enrich response
    property_title = None
    if new_inquiry.property:
        property_title = new_inquiry.property.title
        new_inquiry.property_title = property_title
    
    # Send email notifications
    send_inquiry_admin_notification(
        inquiry_id=new_inquiry.id,
        name=new_inquiry.name,
        email=new_inquiry.email,
        phone=new_inquiry.phone,
        message=new_inquiry.message,
        property_title=property_title
    )
    
    send_inquiry_user_acknowledgement(
        name=new_inquiry.name,
        email=new_inquiry.email,
        property_title=property_title
    )
        
    return new_inquiry
