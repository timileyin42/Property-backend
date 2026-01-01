"""
Email service using Resend for sending notifications
"""

import resend
from app.core.config import settings
from typing import Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Initialize Resend
resend.api_key = settings.RESEND_API_KEY


def load_email_template(template_name: str, **kwargs) -> str:
    """
    Load and render email template
    
    Args:
        template_name: Name of the template file (without .html)
        **kwargs: Variables to replace in template
    
    Returns:
        Rendered HTML content
    """
    template_path = Path(__file__).parent.parent / "templates" / "emails" / f"{template_name}.html"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple template variable replacement
        for key, value in kwargs.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))
        
        return content
    except FileNotFoundError:
        logger.error(f"Email template not found: {template_name}")
        return ""


def send_inquiry_admin_notification(
    inquiry_id: int,
    name: str,
    email: str,
    phone: str,
    message: str,
    property_title: Optional[str] = None
) -> bool:
    """
    Send email notification to admin about new inquiry
    
    Args:
        inquiry_id: ID of the inquiry
        name: Sender's name
        email: Sender's email
        phone: Sender's phone
        message: Inquiry message
        property_title: Optional property title
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        html_content = load_email_template(
            "admin_inquiry_notification",
            inquiry_id=inquiry_id,
            name=name,
            email=email,
            phone=phone,
            message=message,
            property_title=property_title or "General Inquiry"
        )
        
        params = {
            "from": settings.FROM_EMAIL,
            "to": [settings.SALES_EMAIL],
            "subject": f"New Property Inquiry from {name}",
            "html": html_content,
        }
        
        response = resend.Emails.send(params)
        logger.info(f"Admin notification sent for inquiry {inquiry_id}: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send admin notification: {e}")
        return False


def send_inquiry_user_acknowledgement(
    name: str,
    email: str,
    property_title: Optional[str] = None
) -> bool:
    """
    Send acknowledgement email to user who submitted inquiry
    
    Args:
        name: User's name
        email: User's email
        property_title: Optional property title
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        html_content = load_email_template(
            "user_inquiry_acknowledgement",
            name=name,
            property_title=property_title or "our properties"
        )
        
        params = {
            "from": settings.FROM_EMAIL,
            "to": [email],
            "subject": "Thank you for your inquiry - POL Properties",
            "html": html_content,
        }
        
        response = resend.Emails.send(params)
        logger.info(f"User acknowledgement sent to {email}: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send user acknowledgement: {e}")
        return False


def send_verification_otp(
    email: str,
    name: str,
    otp_code: str
) -> bool:
    """
    Send OTP verification email to user
    
    Args:
        email: User's email
        name: User's name
        otp_code: 6-digit OTP code
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        html_content = load_email_template(
            "verification_otp",
            name=name,
            otp_code=otp_code
        )
        
        params = {
            "from": settings.FROM_EMAIL,
            "to": [email],
            "subject": "Verify Your Email - POL Properties",
            "html": html_content,
        }
        
        response = resend.Emails.send(params)
        logger.info(f"Verification OTP sent to {email}: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification OTP: {e}")
        return False


def generate_otp() -> str:
    """
    Generate a 6-digit OTP code
    
    Returns:
        6-digit OTP string
    """
    import random
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


def send_password_reset(
    email: str,
    name: str,
    reset_code: str
) -> bool:
    """
    Send password reset email with reset code
    
    Args:
        email: User's email
        name: User's name
        reset_code: 6-digit reset code
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        html_content = load_email_template(
            "password_reset",
            name=name,
            reset_code=reset_code
        )
        
        params = {
            "from": settings.FROM_EMAIL,
            "to": [email],
            "subject": "Reset Your Password - POL Properties",
            "html": html_content,
        }
        
        response = resend.Emails.send(params)
        logger.info(f"Password reset email sent to {email}: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        return False
