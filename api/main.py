"""
NMAP-AI FastAPI Application
Main entry point for the unified API server

Integrated Pipeline:
- P1: Comprehension & Classification (/comprehend)
- P2: Command Generation (integrated in P4)
- P4: Validation & Decision (/api/validate, /api/generate)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path
import uvicorn

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ============================================================================
# Create FastAPI App
# ============================================================================

app = FastAPI(
    title="NMAP-AI Unified API",
    description="AI-powered Natural Language to Nmap Command Generator with Knowledge Graph RAG and Advanced Validation",
    version="2.0.0",
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

# ============================================================================
# Include Routers
# ============================================================================

# Router 1: P1 Comprehension
try:
    from api.routers import comprehend
    app.include_router(comprehend.router)
    print("✅ P1 Comprehension router loaded")
except ImportError as e:
    print(f"⚠️  Warning: Could not load comprehend router: {e}")

# Router 2: P4 Validator + P2 Generator (Direct Import)
try:
    from api.routers import nmap_ai
    app.include_router(nmap_ai.router, prefix="/api", tags=["NMAP-AI"])
    print("✅ P4 Validator + P2 Generator router loaded (Direct Import)")
except ImportError as e:
    print(f"⚠️  Warning: Could not load nmap_ai router: {e}")
    print("   Make sure nmap_ai.py uses direct P2 import")
except Exception as e:
    print(f"❌ Error loading nmap_ai router: {e}")

# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "NMAP-AI Unified API",
        "version": "2.0.0",
        "description": "Complete P1+P2+P4 Pipeline",
        "integration_mode": "direct_import",
        "architecture": "P1 (comprehension) + P2 (generation via direct import) + P4 (validation)",
        "docs": "/docs",
        "endpoints": {
            "comprehension": {
                "POST /comprehend": "Analyze query complexity (P1)",
                "GET /comprehend/health": "P1 health check"
            },
            "generation_and_validation": {
                "POST /api/generate": "Generate & validate nmap command (P1+P2+P4)",
                "POST /api/validate": "Validate nmap command (P4)",
                "GET /api/status": "Service status"
            },
            "documentation": {
                "GET /docs": "Swagger UI",
                "GET /health": "Global health check"
            }
        }
    }

@app.get("/health")
async def health():
    """Global health check"""
    return {
        "status": "healthy",
        "service": "nmap-ai-unified-api"
    }

# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("\n" + "=" * 70)
    print("🚀 NMAP-AI UNIFIED API STARTING...")
    print("=" * 70)
    print("\n📦 Architecture: P1 + P2 (direct) + P4")
    print("\n📡 Available endpoints:")
    print("   • GET  /              - API info")
    print("   • GET  /health        - Health check")
    print("   • GET  /docs          - Swagger UI")
    print("\n   P1 Comprehension:")
    print("   • POST /comprehend    - Analyze query")
    print("\n   P4 Validation + P2 Generation (integrated):")
    print("   • POST /api/validate  - Validate command")
    print("   • POST /api/generate  - Generate & validate (full pipeline)")
    print("   • GET  /api/status    - Service status")
    print("\n" + "=" * 70)
    print("✅ Server ready at http://localhost:8000")
    print("📚 Documentation at http://localhost:8000/docs")
    print("=" * 70 + "\n")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("\n🛑 NMAP-AI API shutting down...")

# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Starting NMAP-AI Unified API Server")
    print("=" * 70)
    print("\n📍 Server will be available at:")
    print("   • http://localhost:8000")
    print("   • http://localhost:8000/docs (Swagger UI)")
    print("\n💡 Integration Mode: Direct Import (P2 inside P4)")
    print("⚠️  Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )