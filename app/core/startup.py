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
import threading
import time

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
_portfolio_snapshot_thread_started = False


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
    
    start_portfolio_snapshot_scheduler()
    logger.info("✨ Startup tasks completed")


def start_portfolio_snapshot_scheduler():
    global _portfolio_snapshot_thread_started
    if _portfolio_snapshot_thread_started:
        return
    _portfolio_snapshot_thread_started = True
    
    def runner():
        while True:
            db: Session = SessionLocal()
            try:
                from app.services.portfolio_service import create_snapshots_for_all_investors
                create_snapshots_for_all_investors(db)
            except Exception as e:
                logger.error(f"Portfolio snapshot scheduler error: {e}")
            finally:
                db.close()
            time.sleep(24 * 60 * 60)
    
    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
