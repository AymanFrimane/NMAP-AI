"""
NMAP-AI Main API
Point d'entrée principal de l'API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
from pathlib import Path

# Ajouter le dossier api au path
sys.path.insert(0, str(Path(__file__).parent))

# Importer le router
from routers.api import router as nmap_router

# ============================================================================
# APP
# ============================================================================

app = FastAPI(
    title="NMAP-AI API",
    description="API REST pour générer des commandes nmap à partir de langage naturel",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure le router NMAP
app.include_router(nmap_router)

# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["Info"])
async def root():
    """Page d'accueil de l'API"""
    return {
        "message": "NMAP-AI REST API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/nmap/health",
            "generate": "/nmap/generate",
            "batch": "/nmap/generate/batch",
            "services": "/nmap/services",
            "examples": "/nmap/examples"
        }
    }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    """Lance le serveur"""
    
    print("="*70)
    print("🚀 NMAP-AI REST API")
    print("="*70)
    print("📡 Serveur: http://localhost:8000")
    print("📚 Documentation: http://localhost:8000/docs")
    print("🔄 Alternative docs: http://localhost:8000/redoc")
    print("="*70)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
