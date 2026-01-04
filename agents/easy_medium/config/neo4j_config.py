"""
Configuration Neo4j pour NMAP-AI Knowledge Graph
"""

# Neo4j Desktop / Docker Local
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "nmap1234"

# OU pour Neo4j Aura (Cloud)
# NEO4J_URI = "neo4j+s://xxxxx.databases.neo4j.io"
# NEO4J_USER = "neo4j"
# NEO4J_PASSWORD = "ton_mot_de_passe_aura"

# Configuration
NEO4J_DATABASE = "neo4j"  # Nom par défaut
NEO4J_MAX_CONNECTION_LIFETIME = 3600
NEO4J_MAX_CONNECTION_POOL_SIZE = 50