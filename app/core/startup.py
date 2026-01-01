"""
Startup tasks for the application
"""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.user import User, UserRole
from app.utils.hashing import hash_password
import logging

logger = logging.getLogger(__name__)


def create_admin_user():
    """
    Create admin user from environment variables if it doesn't exist
    This runs on application startup
    """
    db: Session = SessionLocal()
    
    try:
        # Check if admin user already exists
        admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        
        if admin:
            logger.info(f" Admin user already exists: {settings.ADMIN_EMAIL}")
            return
        
        # Create admin user
        logger.info(f" Creating admin user: {settings.ADMIN_EMAIL}")
        admin = User(
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            full_name=settings.ADMIN_NAME,
            phone=settings.ADMIN_PHONE,
            role=UserRole.ADMIN,
            is_verified=True  # Admin bypasses email verification
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        logger.info(f" Admin user created successfully: {settings.ADMIN_EMAIL}")
        
    except Exception as e:
        logger.error(f" Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


def startup_tasks():
    """
    Run all startup tasks
    """
    logger.info(" Running startup tasks...")
    create_admin_user()
    logger.info("✨ Startup tasks completed")
