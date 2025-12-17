"""
FastAPI Router pour P2 - Easy/Medium Generator
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.easy_medium.t5_generator import get_generator
import time

# Initialisation du Router
router = APIRouter()

# Modèle de données pour la requête
class GenerateRequest(BaseModel):
    intent: str

# Modèle de données pour la réponse
class GenerateResponse(BaseModel):
    command: str
    complexity: str
    generation_time: float
    model: str = "T5-Stub"

# Endpoint 1 : Génération Easy
@router.post("/generate/easy", response_model=GenerateResponse)
async def generate_easy(request: GenerateRequest):
    """
    Génère une commande EASY complexity
    EASY = Maximum 2 flags, basic scanning
    """
    start_time = time.time()
    
    try:
        generator = get_generator()
        command = generator.generate(request.intent, "EASY")
        
        return GenerateResponse(
            command=command,
            complexity="EASY",
            generation_time=time.time() - start_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint 2 : Génération Medium
@router.post("/generate/medium", response_model=GenerateResponse)
async def generate_medium(request: GenerateRequest):
    """
    Génère une commande MEDIUM complexity
    MEDIUM = 2-4 flags, includes -sV, -O
    """
    start_time = time.time()
    
    try:
        generator = get_generator()
        command = generator.generate(request.intent, "MEDIUM")
        
        return GenerateResponse(
            command=command,
            complexity="MEDIUM",
            generation_time=time.time() - start_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint 3 : Status (bonus)
@router.get("/status")
async def status():
    """Vérifie le statut du générateur P2"""
    try:
        generator = get_generator()
        return {
            "status": "operational",
            "model_ready": generator.model_ready,
            "kg_connected": True,
            "version": "stub"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }