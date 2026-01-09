from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db import init_db
from app.api import api_router
import logging
import sys

# Configure logging to show agent interactions
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set specific loggers to DEBUG level for detailed agent output
logging.getLogger("app.services.chat_service").setLevel(logging.DEBUG)
logging.getLogger("app.agents").setLevel(logging.DEBUG)
logging.getLogger("autogen").setLevel(logging.INFO)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    redirect_slashes=False,  # Disable automatic trailing slash redirects
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Events
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    pass


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to DaveLovable API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
