# tests/conftest.py
import os
import pytest


def pytest_configure(config):
    """Configure environment before tests"""
    # Set Neo4j connection FIRST
    os.environ.setdefault('NEO4J_URI', 'bolt://localhost:7687')
    os.environ.setdefault('NEO4J_USER', 'neo4j')
    os.environ.setdefault('NEO4J_PASSWORD', 'password123')
    
    # Force reload of kg_client with new env vars
    from agents.comprehension import kg_utils
    kg_utils._kg_client = None  # Reset singleton!
    
    print(f"\n✅ Neo4j configured: {os.environ['NEO4J_URI']}")


@pytest.fixture(scope="session", autouse=True)
def neo4j_client():
    """Ensure Neo4j client is properly initialized"""
    from agents.comprehension.kg_utils import get_kg_client
    
    # Force recreation with new env vars
    import agents.comprehension.kg_utils as kg_utils
    kg_utils._kg_client = None
    
    # Now create with correct credentials
    kg = get_kg_client()
    
    if kg.driver:
        print("\n✅ Neo4j connected for tests")
    else:
        print("\n⚠️  Neo4j using fallback mode")
    
    yield kg
    
    # Cleanup
    if kg.driver:
        kg.close()