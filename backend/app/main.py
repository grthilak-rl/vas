from datetime import datetime
from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
import time
import logging

from app.config import settings
from app.database import engine, Base
from app.api import auth, devices, discovery, streams, snapshots
from app.api.dependencies import get_current_user
from app.services.validation import validation_service

# Configure logging
logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="Video Aggregation Service (VAS) - Phase 1 Backend API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(devices.router, prefix=settings.api_v1_prefix)
app.include_router(discovery.router, prefix=settings.api_v1_prefix)
app.include_router(streams.router, prefix=settings.api_v1_prefix)
app.include_router(snapshots.router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    print(f"🚀 {settings.project_name} v{settings.version} started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    print("🛑 Application shutting down")


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to collect API metrics"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # Calculate response time
    response_time = time.time() - start_time
    
    # TODO: Add metrics collection when metrics service is implemented
    
    return response


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.project_name}",
        "version": settings.version,
        "docs": "/docs",
        "health": "/api/health",
        "metrics": "/api/metrics"
    }


@app.get("/api/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.version,
        "database": "unknown",
        "redis": "unknown"
    }
    
    # Check database connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check if ffprobe is available
    try:
        import subprocess
        result = subprocess.run(
            ["ffprobe", "-version"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        if result.returncode == 0:
            health_status["ffprobe"] = "available"
        else:
            health_status["ffprobe"] = "unavailable"
    except Exception:
        health_status["ffprobe"] = "unavailable"
    
    return health_status


@app.get("/api/metrics", tags=["metrics"])
async def get_metrics(
    current_user = Depends(get_current_user)
):
    """Get operational metrics"""
    # TODO: Implement metrics service
    return {
        "message": "Metrics service not yet implemented",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    ) 