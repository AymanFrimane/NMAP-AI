"""
Tests Unitaires pour l'Agent P2 (T5 Generator + KG)
Lancez avec : pytest tests/test_p2.py
"""
import pytest
from pathlib import Path
import sys
import os

# Ajout de la racine au path pour les imports
current_file = Path(__file__).resolve()
project_root = current_file.parent         # Remonte d'1 seul cran (si fichier à la racine)
sys.path.insert(0, str(project_root))

from agents.easy_medium.t5_generator import T5NmapGenerator

# --- FIXTURE : Chargement du modèle une seule fois ---
@pytest.fixture(scope="module")
def generator():
    print("\n⚡ Chargement du modèle pour les tests...")
    # Chemin absolu vers le modèle
    model_path = project_root / "agents/easy_medium/models/nmap_adapter_premium"
    
    if not model_path.exists():
        pytest.fail(f"Modèle introuvable ici : {model_path}")
        
    return T5NmapGenerator(str(model_path))

# --- TESTS ---

def test_kg_integration_ssh(generator):
    """Vérifie que 'ssh' ajoute le port 22 (Preuve que le KG marche)"""
    query = "scan for ssh on 192.168.1.1"
    cmd = generator.generate(query, complexity="MEDIUM")
    print(f"   Query: {query} -> Cmd: {cmd}")
    assert "22" in cmd, "Le port SSH (22) n'a pas été trouvé !"

def test_complexity_filtering_easy(generator):
    """Vérifie que le mode EASY supprime les flags complexes"""
    # On demande des scripts (interdit en EASY)
    query = "scan with scripts and version detection on 10.0.0.1"
    cmd = generator.generate(query, complexity="EASY")
    print(f"   Query: {query} -> Cmd: {cmd}")
    
    # En EASY, on ne doit pas avoir --script
    assert "--script" not in cmd, "Le mode EASY aurait dû filtrer --script"
    # Le mode EASY limite souvent à 1 seul flag non-port
    flags = [x for x in cmd.split() if x.startswith("-") and x != "-p"]
    assert len(flags) <= 1, f"Trop de flags pour EASY : {flags}"

def test_strict_mode_hallucinations(generator):
    """Vérifie que l'agent n'invente pas de ports pour un scan OS"""
    query = "perform OS detection on localhost"
    cmd = generator.generate(query, complexity="MEDIUM")
    print(f"   Query: {query} -> Cmd: {cmd}")
    
    assert "-O" in cmd, "Le flag OS (-O) est manquant"
    # Il ne doit pas y avoir de port 443 ou 80 inventé
    assert "-p" not in cmd, "L'agent a halluciné un port (-p) !"

def test_web_group_resolution(generator):
    """Vérifie que 'web' donne 80 et 443"""
    query = "scan web servers on 192.168.1.50"
    cmd = generator.generate(query, complexity="MEDIUM")
    print(f"   Query: {query} -> Cmd: {cmd}")
    
    assert "80" in cmd, "Port 80 manquant"
    assert "443" in cmd, "Port 443 manquant"

if __name__ == "__main__":
    # Permet de lancer le test directement avec python aussi
    print("Veuillez lancer via 'pytest tests/test_p2.py'")