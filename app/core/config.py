from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Elycapvest Luxury Homes"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_CACHE_TTL: int = 300  # 5 minutes default cache TTL
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_MAX_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: str
    
    # Admin User (auto-created on startup)
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    ADMIN_NAME: str
    ADMIN_PHONE: str
    
    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    CLOUDINARY_UPLOAD_FOLDER: str = "pol-properties"

    # Backblaze B2 (S3-compatible)
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    S3_ENDPOINT: str
    BUCKET_NAME: str

    # Backblaze B2 (native SDK)
    B2_ACCOUNT_ID: str
    B2_APPLICATION_KEY: str
    B2_BUCKET_NAME: str
    B2_API_URL: str
    B2_DOWNLOAD_URL: str
    B2_REGION: str
    
    # Email Configuration (Resend)
    RESEND_API_KEY: str
    ADMIN_EMAIL: str
    SALES_EMAIL: str
    FROM_EMAIL: str
    FRONTEND_URL: str
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Global settings instance
settings = Settings()
