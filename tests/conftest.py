"""Pytest configuration - sets Neo4j env vars"""
import os

def pytest_configure(config):
    """Set environment variables before tests"""
    os.environ.setdefault('NEO4J_URI', 'bolt://localhost:7687')
    os.environ.setdefault('NEO4J_USER', 'neo4j')
    os.environ.setdefault('NEO4J_PASSWORD', 'password123')
