"""
NMAP-AI API (Agent P2)
Ce module expose les endpoints que l'Agent P4 (Orchestrateur) va appeler.
"""
import sys
import logging
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# --- 1. CONFIGURATION DES CHEMINS ---
# Permet de trouver les modules 'agents' depuis le dossier 'api'
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.append(str(project_root))

# --- 2. IMPORT DU GÉNÉRATEUR P2 ---
try:
    from agents.easy_medium.t5_generator import T5NmapGenerator
    AGENTS_LOADED = True
except ImportError as e:
    print(f"❌ Erreur d'import P2: {e}")
    AGENTS_LOADED = False

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("API-P2")

# --- 3. INITIALISATION ---
app = FastAPI(
    title="NMAP-AI P2 Agent API",
    description="Microservice de génération de commandes Nmap (Easy/Medium)",
    version="1.0"
)

# Variable globale pour le générateur
generator = None

@app.on_event("startup")
async def startup_event():
    """Charge le modèle T5 au démarrage de l'API."""
    global generator
    if AGENTS_LOADED:
        try:
            # Chemin vers votre modèle
            model_path = project_root / "agents/easy_medium/models/nmap_adapter_premium"
            
            if model_path.exists():
                logger.info(f"Chargement du modèle depuis: {model_path}")
                generator = T5NmapGenerator(str(model_path))
                logger.info("✅ Agent P2 chargé et prêt à recevoir les requêtes de P4.")
            else:
                logger.error(f"❌ Erreur critique: Dossier modèle introuvable ici: {model_path}")
        except Exception as e:
            logger.error(f"❌ Crash au chargement du modèle: {e}")

# --- 4. MODÈLES DE DONNÉES (Ce que P4 doit envoyer) ---
class NmapRequest(BaseModel):
    query: str

class NmapResponse(BaseModel):
    command: str
    complexity: str
    source: str = "P2-T5"

# --- 5. ENDPOINTS POUR P4 ---

@app.get("/")
def health_check():
    """Vérifie si l'API est en ligne."""
    return {"status": "online", "agent": "P2"}

@app.post("/generate/easy", response_model=NmapResponse)
async def generate_easy(request: NmapRequest):
    """
    Endpoint SPÉCIFIQUE pour le mode EASY.
    P4 appelle ceci quand il veut une commande simple.
    """
    if not generator:
        raise HTTPException(status_code=503, detail="Générateur P2 non initialisé")
    
    logger.info(f"📥 Reçu (EASY): {request.query}")
    
    # Appel au générateur avec contrainte EASY
    cmd = generator.generate(request.query, complexity="EASY")
    
    return {
        "command": cmd,
        "complexity": "EASY"
    }

@app.post("/generate/medium", response_model=NmapResponse)
async def generate_medium(request: NmapRequest):
    """
    Endpoint SPÉCIFIQUE pour le mode MEDIUM.
    P4 appelle ceci quand il veut une commande plus complète.
    """
    if not generator:
        raise HTTPException(status_code=503, detail="Générateur P2 non initialisé")
    
    logger.info(f"📥 Reçu (MEDIUM): {request.query}")
    
    # Appel au générateur avec contrainte MEDIUM
    cmd = generator.generate(request.query, complexity="MEDIUM")
    
    return {
        "command": cmd,
        "complexity": "MEDIUM"
    }

# --- LANCEMENT LOCAL (Pour vos tests) ---
if __name__ == "__main__":
    import uvicorn
    # Lance le serveur sur le port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)