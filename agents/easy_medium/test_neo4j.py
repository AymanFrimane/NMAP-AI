from neo4j import GraphDatabase

# Configuration (ajuste selon ton installation)
URI = "bolt://localhost:7687"  # Neo4j Desktop/Docker
# OU pour Aura: "neo4j+s://xxxxx.databases.neo4j.io"

USERNAME = "neo4j"
PASSWORD = "nmap1234"  # Ton mot de passe

# Test de connexion
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def test_connection():
    with driver.session() as session:
        result = session.run("RETURN 'Hello from Python!' AS message")
        for record in result:
            print(record["message"])

try:
    test_connection()
    print("✅ Connexion réussie !")
except Exception as e:
    print(f"❌ Erreur : {e}")
finally:
    driver.close()