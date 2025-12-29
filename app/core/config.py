from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "POL Properties"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: str
    
    # Admin User (auto-created on startup)
    ADMIN_EMAIL: str = "admin@plugoflagosproperty.com"
    ADMIN_PASSWORD: str = "ChangeThisPassword123!"
    ADMIN_NAME: str = "System Administrator"
    ADMIN_PHONE: str = "+234-800-000-0001"
    
    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    CLOUDINARY_UPLOAD_FOLDER: str = "pol-properties"
    
    # Email Configuration (Resend)
    RESEND_API_KEY: str
    ADMIN_EMAIL: str = "admin@plugoflagosproperty.com"  # Reuse from admin user
    SALES_EMAIL: str = "sales@polproperties.com"  # Sales team email
    FROM_EMAIL: str = "noreply@polproperties.com"  # Sender email
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
