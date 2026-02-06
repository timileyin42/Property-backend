from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.startup import startup_tasks
from app.api import auth, public, admin, investor, media, user, files
from app.api import shortlet, investor_shortlet, inquiries, contact
from app.utils.redis_client import increment
import logging
import time

logger = logging.getLogger(__name__)


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
    description="Property Investment Platform API - Elycap Luxury Homes",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if not settings.RATE_LIMIT_ENABLED:
        return await call_next(request)
    if request.method == "OPTIONS":
        return await call_next(request)
    if request.url.path in {"/health", "/docs", "/redoc", "/openapi.json"}:
        return await call_next(request)
    forwarded_for = request.headers.get("x-forwarded-for")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else None
    if not client_ip and request.client:
        client_ip = request.client.host
    if not client_ip:
        return await call_next(request)
    window_seconds = settings.RATE_LIMIT_WINDOW_SECONDS
    window_key = int(time.time() // window_seconds)
    key = f"rate:{client_ip}:{window_key}"
    counter = increment(key, 1, ttl=window_seconds)
    if counter is None:
        return await call_next(request)
    if counter > settings.RATE_LIMIT_MAX_REQUESTS:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )
    return await call_next(request)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and responses"""
    start_time = time.time()
    
    # Log request
    logger.info(f"→ {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"← {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Time: {process_time:.3f}s"
    )
    
    return response

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
app.include_router(user.router)
app.include_router(admin.router)
app.include_router(investor.router)
app.include_router(media.router)
app.include_router(files.router)
app.include_router(shortlet.router)
app.include_router(investor_shortlet.router)
app.include_router(inquiries.router)
app.include_router(contact.router)


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Welcome Elycapvest Luxury Homes API",
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
