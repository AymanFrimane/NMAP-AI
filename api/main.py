"""
NMAP-AI FastAPI Application
Main entry point for the REST API
Person 4's API endpoints for validation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="NMAP-AI API",
    description="AI-powered Natural Language to Nmap Command Generator with Advanced Validation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/")
async def root():
    """
    Root endpoint - API status
    
    Returns basic API information
    """
    return {
        "status": "online",
        "message": "NMAP-AI API is running",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "validate": "/api/validate",
            "generate": "/api/generate"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for Docker
    
    Returns:
        Simple health status
    """
    return {"status": "healthy"}


# ============================================================================
# Include Routers
# ============================================================================

# Import and include the NMAP-AI router
try:
    from api.routers import nmap_ai
    app.include_router(nmap_ai.router, prefix="/api", tags=["NMAP-AI"])
    print("✅ NMAP-AI router loaded successfully")
except ImportError as e:
    print(f"⚠️  Warning: Could not load nmap_ai router: {e}")
    print("   API will work but /api/validate and /api/generate won't be available")
except Exception as e:
    print(f"❌ Error loading nmap_ai router: {e}")


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Run on application startup
    """
    print("=" * 70)
    print("🚀 NMAP-AI API Starting...")
    print("=" * 70)
    print("\n📡 Available endpoints:")
    print("   • GET  /          - API info")
    print("   • GET  /health    - Health check")
    print("   • GET  /docs      - Swagger UI")
    print("   • POST /api/validate - Validate nmap command")
    print("   • POST /api/generate - Generate nmap command")
    print("\n" + "=" * 70 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Run on application shutdown
    """
    print("\n🛑 NMAP-AI API shutting down...")


# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Starting NMAP-AI API Server")
    print("=" * 70)
    print("\n📍 Server will be available at:")
    print("   • http://localhost:8000")
    print("   • http://localhost:8000/docs (Swagger UI)")
    print("\n⚠️  Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )