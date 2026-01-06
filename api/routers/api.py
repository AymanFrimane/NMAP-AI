"""
NMAP-AI REST API
API REST professionnelle pour générer des commandes nmap
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import sys
from pathlib import Path

# Ajouter le path vers knowledge_graph
knowledge_graph_path = Path(__file__).parent.parent.parent / 'knowledge_graph'
sys.path.insert(0, str(knowledge_graph_path))

from final_nmap_pipeline import FinalNmapPipeline

# ============================================================================
# MODELS
# ============================================================================

class NmapQuery(BaseModel):
    """Requête pour générer une commande nmap"""
    query: str = Field(..., description="Requête en langage naturel", example="scan for web servers on 192.168.1.0/24")
    use_rag: bool = Field(True, description="Utiliser le Knowledge Graph RAG")

class NmapCommand(BaseModel):
    """Commande nmap générée"""
    query: str
    command: str
    services: List[str] = []
    explanation: str
    raw_command: Optional[str] = None

class BatchQuery(BaseModel):
    """Requêtes multiples"""
    queries: List[str] = Field(..., description="Liste de requêtes")
    use_rag: bool = Field(True, description="Utiliser le RAG")

class HealthCheck(BaseModel):
    """État de santé de l'API"""
    status: str
    kg_connected: bool
    t5_loaded: bool

# ============================================================================
# ROUTER
# ============================================================================

from fastapi import APIRouter

router = APIRouter(
    prefix="/nmap",
    tags=["NMAP-AI"]
)

# Pipeline global
pipeline = None

# ============================================================================
# STARTUP
# ============================================================================

def initialize_pipeline():
    """Initialise le pipeline"""
    global pipeline
    
    print("🚀 Initialisation du pipeline NMAP-AI...")
    
    try:
        pipeline = FinalNmapPipeline()
        print("✅ Pipeline initialisé avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation : {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Vérifie l'état de santé de l'API"""
    
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline non initialisé")
    
    return {
        "status": "healthy",
        "kg_connected": True,
        "t5_loaded": True
    }

@router.post("/generate", response_model=NmapCommand)
async def generate_command(query: NmapQuery):
    """
    Génère une commande nmap à partir d'une requête en langage naturel
    
    **Exemples de requêtes :**
    - "scan for web servers on 192.168.1.0/24"
    - "scan for SSH on 10.0.0.1"
    - "perform OS detection on 172.16.0.1"
    - "scan all ports on 192.168.1.1"
    - "scan for DNS, SNMP and Telnet on 172.16.0.254"
    """
    
    if not pipeline:
        # Essayer d'initialiser
        if not initialize_pipeline():
            raise HTTPException(status_code=503, detail="Pipeline non initialisé")
    
    try:
        result = pipeline.generate(query.query, use_rag=query.use_rag)
        
        return {
            "query": result['query'],
            "command": result['final_command'],
            "services": result['services'],
            "explanation": result['explanation'],
            "raw_command": result.get('raw_command')
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération : {str(e)}")

@router.post("/generate/batch", response_model=List[NmapCommand])
async def generate_batch(batch: BatchQuery):
    """
    Génère plusieurs commandes nmap en une seule requête
    
    **Exemple :**
    ```json
    {
      "queries": [
        "scan for web servers on 192.168.1.0/24",
        "scan for SSH on 10.0.0.1"
      ]
    }
    ```
    """
    
    if not pipeline:
        if not initialize_pipeline():
            raise HTTPException(status_code=503, detail="Pipeline non initialisé")
    
    try:
        results = []
        
        for query_text in batch.queries:
            result = pipeline.generate(query_text, use_rag=batch.use_rag)
            
            results.append({
                "query": result['query'],
                "command": result['final_command'],
                "services": result['services'],
                "explanation": result['explanation'],
                "raw_command": result.get('raw_command')
            })
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération : {str(e)}")

@router.get("/services")
async def list_services():
    """
    Liste tous les services disponibles dans le Knowledge Graph
    """
    
    if not pipeline:
        if not initialize_pipeline():
            raise HTTPException(status_code=503, detail="Pipeline non initialisé")
    
    try:
        query = """
        MATCH (s:Service)
        OPTIONAL MATCH (p:Port)-[:HOSTS]->(s)
        RETURN s.name AS service,
               s.category AS category,
               collect(DISTINCT p.number) AS ports
        ORDER BY s.category, s.name
        """
        
        with pipeline.kg_rag.driver.session() as session:
            result = session.run(query)
            services = [dict(record) for record in result]
        
        return {
            "count": len(services),
            "services": services
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur : {str(e)}")

@router.get("/services/{service_name}")
async def get_service_info(service_name: str):
    """
    Récupère les informations détaillées d'un service
    
    **Exemples :**
    - /services/HTTP
    - /services/SSH
    - /services/DNS
    """
    
    if not pipeline:
        if not initialize_pipeline():
            raise HTTPException(status_code=503, detail="Pipeline non initialisé")
    
    try:
        info = pipeline.kg_rag.get_service_info(service_name)
        
        if not info:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' non trouvé")
        
        return info
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur : {str(e)}")

@router.get("/examples")
async def get_examples():
    """
    Retourne des exemples de requêtes
    """
    
    return {
        "examples": [
            {
                "category": "Services",
                "queries": [
                    "scan for web servers on 192.168.1.0/24",
                    "scan for SSH on 10.0.0.1",
                    "scan for DNS, SNMP and Telnet on 172.16.0.254",
                    "scan for database services on 192.168.0.0/24"
                ]
            },
            {
                "category": "Scan Types",
                "queries": [
                    "do a ping scan on 10.0.0.0/24",
                    "scan all ports on 192.168.1.1",
                    "perform OS detection on 172.16.0.1"
                ]
            },
            {
                "category": "Advanced",
                "queries": [
                    "aggressive scan with scripts on 10.0.0.1",
                    "fast scan for web servers on 192.168.1.0/24",
                    "stealth scan for SSH on 10.0.0.1"
                ]
            }
        ]
    }

# ============================================================================
# Initialisation au chargement du module
# ============================================================================

# Initialiser le pipeline quand le router est chargé
initialize_pipeline()