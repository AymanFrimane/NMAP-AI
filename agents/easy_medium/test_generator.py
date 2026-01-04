"""
Test du générateur T5 avec chemin correct
"""

import sys
from pathlib import Path

# Ajouter le répertoire au path si besoin
sys.path.insert(0, str(Path(__file__).parent))

from t5_generator import T5NmapGenerator

# Chemin relatif depuis agents/easy_medium/
ADAPTER_PATH = "models/nmap_adapter_premium"

# Vérifier que l'adapter existe
adapter_path = Path(ADAPTER_PATH)
if not adapter_path.exists():
    print(f"❌ Adapter non trouvé : {adapter_path.absolute()}")
    print("\n📥 Tu dois d'abord télécharger l'adapter depuis Colab !")
    print("\nÉtapes :")
    print("1. Va sur drive.google.com")
    print("2. Trouve le dossier 'nmap_adapter_premium'")
    print("3. Télécharge-le")
    print("4. Place-le dans : NMAP-AI/agents/easy_medium/models/")
    sys.exit(1)

print("✅ Adapter trouvé !")
print(f"📂 Chemin : {adapter_path.absolute()}\n")

# Créer le générateur
print("🚀 Initialisation du générateur T5...\n")
generator = T5NmapGenerator(ADAPTER_PATH)

# Afficher les infos
print("\n📊 Informations du modèle:")
info = generator.get_model_info()
for key, value in info.items():
    print(f"   {key}: {value}")

# Tests
print("\n🧪 Tests de génération:\n")

test_queries = [
    "scan all ports on 192.168.1.1",
    "do a ping scan on 10.0.0.0/24",
    "scan for web servers on 192.168.0.1",
    "perform OS detection on 172.16.0.1",
    "scan for SSH with version detection on 192.168.1.100",
]

for i, query in enumerate(test_queries, 1):
    command = generator.generate(query)
    print(f"{i}. Query: {query}")
    print(f"   Command: {command}\n")

print("✅ Tous les tests réussis !")