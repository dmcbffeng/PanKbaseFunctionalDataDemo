"""
PanKbase Functional Data API

FastAPI application for querying and analyzing human pancreas perifusion data.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import filter_router, analysis_router, integration_router
from app.services.data_loader import data_loader


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - load data on startup"""
    print("Loading data...")
    try:
        data_loader.load_all()
        print("Data loaded successfully!")
    except Exception as e:
        print(f"Error loading data: {e}")
        raise
    
    yield
    
    # Cleanup on shutdown (if needed)
    print("Shutting down...")


app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(filter_router)
app.include_router(analysis_router)
app.include_router(integration_router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "docs": "/docs",
        "endpoints": {
            "filter": {
                "metadata": "/api/filter/metadata",
                "donors": "/api/filter/donors",
                "timeseries": "/api/filter/timeseries",
                "traits": "/api/filter/traits",
                "download": "/api/filter/download"
            },
            "analysis": {
                "variables": "/api/analysis/variables",
                "association": "/api/analysis/association",
                "methods": "/api/analysis/methods",
                "traits": "/api/analysis/traits"
            },
            "integration": {
                "sources": "/api/integration/sources",
                "analyze": "/api/integration/analyze",
                "donors": "/api/integration/donors",
                "validate": "/api/integration/validate"
            }
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "data_loaded": data_loader._initialized,
        "donors_count": len(data_loader.merged_df) if data_loader._merged_df is not None else 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
