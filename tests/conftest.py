"""
Pytest configuration for NMAP-AI tests
Configures environment variables for Neo4j connection
"""

import os
import pytest


def pytest_configure(config):
    """Configure environment before tests run"""
    # Set Neo4j connection for tests
    os.environ.setdefault('NEO4J_URI', 'bolt://localhost:7687')
    os.environ.setdefault('NEO4J_USER', 'neo4j')
    os.environ.setdefault('NEO4J_PASSWORD', 'password123')
    
    print("\n" + "="*70)
    print("PYTEST CONFIGURATION")
    print("="*70)
    print(f"Neo4j URI: {os.environ.get('NEO4J_URI')}")
    print(f"Neo4j User: {os.environ.get('NEO4J_USER')}")
    print("="*70 + "\n")


@pytest.fixture(scope="session", autouse=True)
def neo4j_check():
    """Check if Neo4j is available before integration tests"""
    from agents.comprehension.kg_utils import get_kg_client
    
    kg = get_kg_client()
    
    if kg.driver:
        print("\n✅ Neo4j is available for integration tests")
    else:
        print("\n⚠️  Neo4j not available - integration tests will be skipped")
    
    yield kg
    
    # Cleanup
    if kg.driver:
        kg.close()
