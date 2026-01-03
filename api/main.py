"""
NMAP-AI FastAPI Application
Main entry point for the API server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.routers import comprehend


# Create FastAPI app
app = FastAPI(
    title="NMAP-AI API",
    description="Autonomous Nmap Command Generator with Knowledge Graph RAG",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(comprehend.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "NMAP-AI API",
        "version": "1.0.0",
        "description": "Autonomous Nmap Command Generator",
        "docs": "/docs",
        "endpoints": {
            "comprehension": "/comprehend",
            "health": "/comprehend/health"
        }
    }


@app.get("/health")
async def health():
    """Global health check."""
    return {
        "status": "healthy",
        "service": "nmap-ai-api"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)