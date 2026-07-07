"""FastAPI application with all routes and middleware."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import SlowApi, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from contextlib import asynccontextmanager

from app.utils.config import settings
from app.models.database import init_db
from app.api import auth, emails, ai, templates, contacts, analytics, schedule

# Rate limiter
limiter = SlowApi(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - initialize database on startup."""
    # Startup
    init_db()
    print("✅ Database initialized")
    print(f"🚀 {settings.app_name} is running!")
    yield
    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered Gmail Assistant for automated email generation and management",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "description": "AI-powered Gmail Assistant",
        "docs": "/docs",
        "status": "running"
    }


# Health check endpoint
@app.get("/health")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def health_check(request: Request):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name
    }


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(emails.router, prefix="/api/emails", tags=["Emails"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["Contacts"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(schedule.router, prefix="/api/schedule", tags=["Schedule"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
