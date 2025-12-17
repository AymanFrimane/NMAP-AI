"""
Knowledge Graph RAG - Mock Version
Simule Neo4j en attendant que P1 termine son travail
"""
from typing import List

class KnowledgeGraphRAG:
    """Mock du Knowledge Graph pour développement indépendant de P1"""
    
    def __init__(self):
        print("⚠️  [P2] Using MOCK Knowledge Graph (no Neo4j connection)")
        
        # Flags autorisés pour EASY (simple scans)
        self._easy_flags = [
            '-sT',           # TCP connect scan
            '-p',            # Port specification
            '--top-ports',   # Common ports
            '-F',            # Fast scan
        ]
        
        # Flags autorisés pour MEDIUM (intermediate scans)
        self._medium_flags = [
            '-sT', '-sS',                      # Scan types
            '-p', '-p-', '--top-ports',        # Port specs
            '-sV',                             # Version detection
            '-O',                              # OS detection
            '-Pn',                             # No ping
            '-n',                              # No DNS
            '-T0', '-T1', '-T2', '-T3', '-T4', # Timing
            '-v', '-vv',                       # Verbosity
        ]
    
    def get_allowed_flags_easy(self) -> List[str]:
        """Retourne les flags autorisés pour EASY complexity"""
        return self._easy_flags.copy()
    
    def get_allowed_flags_medium(self) -> List[str]:
        """Retourne les flags autorisés pour MEDIUM complexity"""
        return self._medium_flags.copy()


# Singleton instance
_kg_instance = None

def get_kg() -> KnowledgeGraphRAG:
    """Retourne l'instance singleton du Knowledge Graph"""
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = KnowledgeGraphRAG()
    return _kg_instance