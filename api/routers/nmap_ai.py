from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.easy_medium.t5_generator import T5Generator

# Initialisation du Router et du Générateur
router = APIRouter()
generator = T5Generator()

# Modèle de données (Ce que l'utilisateur doit envoyer)
class GenerateRequest(BaseModel):
    intent: str
    complexity: str = "EASY"  # Valeur par défaut

# Endpoint 1 : Génération Easy
@router.post("/generate/easy")
async def generate_easy(request: GenerateRequest):
    try:
        command = generator.generate(request.intent, "EASY")
        return {"command": command, "model": "T5-Stub"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint 2 : Génération Medium
@router.post("/generate/medium")
async def generate_medium(request: GenerateRequest):
    try:
        command = generator.generate(request.intent, "MEDIUM")
        return {"command": command, "model": "T5-Stub"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))