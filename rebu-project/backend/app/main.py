"""
Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.workers.background_workers import workers
from urllib.parse import urlparse

# Import routers
from app.api import auth, trips, drivers, users, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events: startup and shutdown"""
    # Startup
    print("🚀 Starting Rebu API...")
    
    # Initialize database
    init_db()
    print("✅ Database initialized")
    
    # Start background workers
    workers.start()
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Rebu API...")
    workers.stop()


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(drivers.router, prefix=f"{settings.API_V1_STR}/drivers", tags=["Drivers"])
app.include_router(trips.router, prefix=f"{settings.API_V1_STR}/trips", tags=["Trips"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["Admin"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Rebu API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from app.core.redis_client import redis_client
    
    redis_status = "connected" if redis_client.ping() else "disconnected"
    
    return {
        "status": "healthy",
        "redis": redis_status,
        "timestamp": "2026-01-27T10:00:00Z"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
