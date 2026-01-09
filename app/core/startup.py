"""
Startup tasks for the application
"""

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.user import User, UserRole
from app.utils.hashing import hash_password
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Enable SQLAlchemy query logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

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
            message = f"Admin user already exists: {settings.ADMIN_EMAIL}"
            logger.info(message)
            print(message)
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
        
        message = f"Admin user created successfully: {settings.ADMIN_EMAIL}"
        logger.info(message)
        print(message)
        
    except Exception as e:
        logger.error(f" Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


def startup_tasks():
    """
    Run all startup tasks
    """
    logger.info("🚀 Running startup tasks...")
    
    # Initialize database
    create_admin_user()
    
    # Initialize Redis connection
    try:
        from app.utils.redis_client import get_redis
        redis_client = get_redis()
        redis_client.ping()
        logger.info("✅ Redis connection established")
    except Exception as e:
        logger.warning(f"⚠️  Redis connection failed: {e}")
        logger.warning("   Application will continue without Redis caching")
    
    logger.info("✨ Startup tasks completed")
