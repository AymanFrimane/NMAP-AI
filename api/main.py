from fastapi import FastAPI
from api.routers import nmap_ai

app = FastAPI(title="NMAP-AI Agent", version="1.0.0")

# Inclusion de votre router P2
app.include_router(nmap_ai.router, tags=["P2-Generator"])

@app.get("/")
def read_root():
    return {"status": "System Online", "modules": ["P2-EasyMedium"]}