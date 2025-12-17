"""
T5 Generator - Version Stub avec Knowledge Graph
"""
import time
from agents.easy_medium.kg_rag import get_kg

class T5Generator:
    def __init__(self):
        print("✅ [P2] Initializing T5 Generator (Stub version)")
        self.model_ready = True
        self.kg = get_kg()  # Connexion au Knowledge Graph
    
    def generate(self, intent: str, complexity: str) -> str:
        """
        Génère une commande Nmap selon l'intention et la complexité
        
        Args:
            intent: Description en langage naturel
            complexity: "EASY" ou "MEDIUM" (déterminé par P1 ou par l'endpoint)
        
        Returns:
            Commande nmap générée
        """
        # Simule un temps de calcul (< 2s requis par Issue #15)
        time.sleep(0.1)
        
        intent_lower = intent.lower()
        
        # Récupérer les flags autorisés depuis le KG
        if complexity == "EASY":
            allowed_flags = self.kg.get_allowed_flags_easy()
        else:
            allowed_flags = self.kg.get_allowed_flags_medium()
        
        # Logique de génération basée sur des patterns
        command = "nmap"
        
        # Pattern: Web scanning
        if "web" in intent_lower or "http" in intent_lower:
            if "-p" in allowed_flags:
                command += " -p 80,443"
            if complexity == "MEDIUM" and "-sV" in allowed_flags:
                command += " -sV"
        
        # Pattern: SSH
        elif "ssh" in intent_lower:
            if "-p" in allowed_flags:
                command += " -p 22"
            if complexity == "MEDIUM" and "-sV" in allowed_flags:
                command += " -sV"
        
        # Pattern: Database
        elif "database" in intent_lower or "db" in intent_lower:
            if "-p" in allowed_flags:
                command += " -p 3306,5432"
            if complexity == "MEDIUM" and "-sV" in allowed_flags:
                command += " -sV"
        
        # Pattern: OS Detection
        elif "os" in intent_lower or "operating system" in intent_lower:
            if complexity == "MEDIUM" and "-O" in allowed_flags:
                command += " -O"
                if "-sV" in allowed_flags:
                    command += " -sV"
            else:
                command += " -F"
        
        # Default MEDIUM
        elif complexity == "MEDIUM":
            if "-sV" in allowed_flags:
                command += " -sV"
            if "-O" in allowed_flags:
                command += " -O --version-intensity 5"
        
        # Default EASY
        else:
            if "-F" in allowed_flags:
                command += " -F"
        
        # Ajouter target placeholder
        command += " <target>"
        
        return command


# Singleton instance
_generator = None

def get_generator() -> T5Generator:
    """Retourne l'instance singleton du générateur"""
    global _generator
    if _generator is None:
        _generator = T5Generator()
    return _generator