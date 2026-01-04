from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.startup import startup_tasks
from app.api import auth, public, admin, investor, media
from app.api import shortlet, investor_shortlet, inquiries


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler - runs on startup and shutdown
    """
    # Startup
    startup_tasks()
    yield
    # Shutdown (if needed)


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Property Investment Platform API - POL Properties",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(public.router)
app.include_router(admin.router)
app.include_router(investor.router)
app.include_router(media.router)
app.include_router(shortlet.router)
app.include_router(investor_shortlet.router)
app.include_router(inquiries.router)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Welcome to POL Properties API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint with database and Redis status"""
    from app.utils.redis_client import health_check as redis_health
    from app.core.database import get_db
    
    # Check database
    db_status = {"status": "healthy", "connected": True}
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        db.close()
    except Exception as e:
        db_status = {"status": "unhealthy", "connected": False, "error": str(e)}
    
    # Check Redis
    redis_status = redis_health()
    
    # Overall status
    overall_healthy = (
        db_status.get("status") == "healthy" and 
        redis_status.get("status") == "healthy"
    )
    
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": db_status,
        "redis": redis_status
    }
