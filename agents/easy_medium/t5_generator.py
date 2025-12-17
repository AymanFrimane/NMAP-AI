import time

class T5Generator:
    def __init__(self):
        # Simulation du chargement du modèle
        print("P2 [INFO]: Chargement du modèle T5-Stub...")
        self.model_ready = True

    def generate(self, intent: str, complexity: str) -> str:
        """
        Fonction principale appelée par l'API.
        Pour le Sprint 1, elle retourne des règles simples.
        """
        # On simule un petit temps de calcul (< 2s demandé par l'issue #15)
        time.sleep(0.1)

        intent_lower = intent.lower()

        # Logique 'Stub' (Fausse IA) en attendant le fine-tuning
        if "scan" in intent_lower and "web" in intent_lower:
            return "nmap -p 80,443 -sV <target>"
        
        if complexity == "MEDIUM":
            return "nmap -sV -O --version-intensity 5 <target>"
            
        # Par défaut (EASY)
        return "nmap -F <target>"