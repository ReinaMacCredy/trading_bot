from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn

from src.web.routers import api_router
from src.web.dependencies import life_span

from src.web.config import (
    API_TITLE,
    API_DESCRIPTION,
    API_VERSION,
    API_TERMS_OF_SERVICE,
    API_CONTACT,
    API_LICENSE_INFO,
    TAGS_METADATA
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    terms_of_service=API_TERMS_OF_SERVICE,
    contact=API_CONTACT,
    license_info=API_LICENSE_INFO,
    openapi_tags=TAGS_METADATA,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc UI
    openapi_url="/openapi.json",  # OpenAPI schema
    lifespan=life_span
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI server"""
    uvicorn.run(
        "src.web.server:app",
        host=host,
        port=port,
        reload=True
    )

if __name__ == "__main__":
    start_server() 