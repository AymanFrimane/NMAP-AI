import requests
import json

# L'adresse de VOTRE API (P2)
API_URL = "http://127.0.0.1:8000"

def simulate_p4_call(query, complexity):
    print(f"\n🤖 P4 demande ({complexity}): '{query}'")
    
    endpoint = f"{API_URL}/generate/{complexity.lower()}"
    
    try:
        response = requests.post(endpoint, json={"query": query})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ P2 a répondu : {data['command']}")
        else:
            print(f"❌ Erreur P2 : {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ P4 n'arrive pas à joindre P2. L'API est-elle lancée ? ({e})")

# --- SCÉNARIO DE TEST ---
if __name__ == "__main__":
    # Test 1: EASY (Doit être filtré)
    simulate_p4_call("scan for web servers on 192.168.1.1 with scripts", "EASY")
    
    # Test 2: MEDIUM (Doit être plus complet)
    simulate_p4_call("scan for web servers on 192.168.1.1 with scripts", "MEDIUM")