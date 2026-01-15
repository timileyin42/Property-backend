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
        
        context = {
            "app_name": settings.APP_NAME,
            **kwargs,
        }
        
        for key, value in context.items():
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
        if not html_content:
            logger.error("Email content is empty for user inquiry acknowledgement")
            return False
        
        params = {
            "from": settings.FROM_EMAIL,
            "to": [email],
            "subject": f"Thank you for your inquiry - {settings.APP_NAME}",
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
        if not html_content:
            logger.error("Email content is empty for verification OTP")
            return False
        
        params = {
            "from": settings.FROM_EMAIL,
            "to": [email],
            "subject": f"Verify Your Email - {settings.APP_NAME}",
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
        if not html_content:
            logger.error("Email content is empty for password reset")
            return False
        
        params = {
            "from": settings.FROM_EMAIL,
            "to": [email],
            "subject": f"Reset Your Password - {settings.APP_NAME}",
            "html": html_content,
        }
        
        response = resend.Emails.send(params)
        logger.info(f"Password reset email sent to {email}: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        return False


def send_application_admin_notification(
    application_id: int,
    user_name: str,
    user_email: str,
    motivation: str,
    investment_amount: Optional[float] = None,
    experience: Optional[str] = None
) -> bool:
    """
    Send email notification to admin about new investment application
    
    Args:
        application_id: ID of the application
        user_name: Applicant's name
        user_email: Applicant's email
        motivation: Why they want to invest
        investment_amount: Expected investment amount
        experience: Investment experience
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        html_content = load_email_template(
            "admin_application_notification",
            application_id=application_id,
            user_name=user_name,
            user_email=user_email,
            motivation=motivation,
            investment_amount=f"${investment_amount:,.2f}" if investment_amount else "Not specified",
            experience=experience or "Not specified",
            admin_dashboard_url=f"{settings.FRONTEND_URL}/admin/applications"
        )
        if not html_content:
            logger.error("Email content is empty for admin application notification")
            return False
        
        params = {
            "from": settings.FROM_EMAIL,
            "to": [settings.SALES_EMAIL],
            "subject": f"New Investment Application from {user_name}",
            "html": html_content,
        }
        
        response = resend.Emails.send(params)
        logger.info(f"Admin notification sent for application {application_id}: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send admin application notification: {e}")
        return False


def send_application_approved(
    email: str,
    name: str,
    admin_notes: Optional[str] = None
) -> bool:
    """
    Send email notification to user that their application was approved
    
    Args:
        email: User's email
        name: User's name
        admin_notes: Optional notes from admin
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        # Format admin notes if present
        notes_html = ""
        if admin_notes:
            notes_html = f'''
            <div class="admin-note">
                <strong>Message from our team:</strong><br>
                {admin_notes}
            </div>
            '''
        
        html_content = load_email_template(
            "application_approved",
            user_name=name,
            admin_notes=notes_html,
            investor_dashboard_url=f"{settings.FRONTEND_URL}/investor/dashboard",
            support_email=settings.FROM_EMAIL
        )
        if not html_content:
            logger.error("Email content is empty for application approval")
            return False
        
        params = {
            "from": settings.FROM_EMAIL,
            "to": [email],
            "subject": f"🎉 Welcome to {settings.APP_NAME} - You're Now an Investor!",
            "html": html_content,
        }
        
        response = resend.Emails.send(params)
        logger.info(f"Application approval email sent to {email}: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send application approval email: {e}")
        return False


def send_application_rejected(
    email: str,
    name: str,
    rejection_reason: Optional[str] = None
) -> bool:
    """
    Send email notification to user that their application was rejected
    
    Args:
        email: User's email
        name: User's name
        rejection_reason: Reason for rejection
    
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        # Format rejection reason if present
        reason_html = ""
        if rejection_reason:
            reason_html = f'''
            <div class="reason-box">
                <strong>Reason:</strong><br>
                {rejection_reason}
            </div>
            '''
        
        html_content = load_email_template(
            "application_rejected",
            user_name=name,
            rejection_reason=reason_html,
            support_email=settings.FROM_EMAIL
        )
        if not html_content:
            logger.error("Email content is empty for application rejection")
            return False
        
        params = {
            "from": settings.FROM_EMAIL,
            "to": [email],
            "subject": f"Investment Application Update - {settings.APP_NAME}",
            "html": html_content,
        }
        
        response = resend.Emails.send(params)
        logger.info(f"Application rejection email sent to {email}: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send application rejection email: {e}")
        return False
