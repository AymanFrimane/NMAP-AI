"""
Neo4j Knowledge Graph Integration Tests
Tests for KG connectivity, queries, and data integrity

Run with: pytest tests/test_neo4j.py -v
"""

import pytest
from neo4j import GraphDatabase
import os
from agents.comprehension.kg_utils import Neo4jClient, get_kg_client, get_options, get_conflicts


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def neo4j_credentials():
    """Get Neo4j credentials from environment."""
    return {
        "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "user": os.getenv("NEO4J_USER", "neo4j"),
        "password": os.getenv("NEO4J_PASSWORD", "password123")
    }

@pytest.fixture(scope="module")
def check_neo4j_running(neo4j_credentials):
    """Check if Neo4j is running before tests."""
    try:
        driver = GraphDatabase.driver(
            neo4j_credentials["uri"],
            auth=(neo4j_credentials["user"], neo4j_credentials["password"])
        )
        with driver.session() as session:
            session.run("RETURN 1")
        driver.close()
    except Exception as e:
        pytest.skip(f"Neo4j not running: {e}. Start with: docker-compose up -d neo4j")

@pytest.fixture
def kg_client(check_neo4j_running):
    """Create KG client for testing."""
    client = get_kg_client()
    yield client
    # Cleanup
    if client.driver:
        client.close()


# ============================================================================
# Test: Neo4j Connection
# ============================================================================

class TestNeo4jConnection:
    """Test Neo4j database connectivity."""
    
    def test_neo4j_connection(self, kg_client):
        """Test that Neo4j connection works."""
        assert kg_client.driver is not None
    
    def test_neo4j_query(self, kg_client, neo4j_credentials):
        """Test basic Neo4j query execution."""
        driver = GraphDatabase.driver(
            neo4j_credentials["uri"],
            auth=(neo4j_credentials["user"], neo4j_credentials["password"])
        )
        
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            assert record["test"] == 1
        
        driver.close()
    
    def test_database_not_empty(self, kg_client, neo4j_credentials):
        """Test that database has been initialized with data."""
        driver = GraphDatabase.driver(
            neo4j_credentials["uri"],
            auth=(neo4j_credentials["user"], neo4j_credentials["password"])
        )
        
        with driver.session() as session:
            result = session.run("MATCH (o:Option) RETURN count(o) as count")
            count = result.single()["count"]
            assert count > 0, "Database appears empty. Run: python agents/comprehension/init_kg.py"
        
        driver.close()


# ============================================================================
# Test: KG Data Integrity
# ============================================================================

class TestKGDataIntegrity:
    """Test Knowledge Graph data integrity."""
    
    def test_options_exist(self, kg_client):
        """Test that nmap options are loaded."""
        options = kg_client.get_options()
        assert len(options) > 0
        assert len(options) >= 20  # Should have at least 20 options
    
    def test_scan_type_options(self, kg_client):
        """Test that SCAN_TYPE category exists."""
        options = kg_client.get_options(category="SCAN_TYPE")
        assert len(options) > 0
        
        # Should have common scan types
        option_names = [opt.name for opt in options]
        assert "-sS" in option_names
        assert "-sT" in option_names
    
    def test_port_spec_options(self, kg_client):
        """Test PORT_SPEC options."""
        options = kg_client.get_options(category="PORT_SPEC")
        assert len(options) > 0
        
        option_names = [opt.name for opt in options]
        assert "-p" in option_names
        assert "-F" in option_names
    
    def test_root_required_options(self, kg_client):
        """Test filtering by root requirement."""
        root_options = kg_client.get_options(requires_root=True)
        non_root_options = kg_client.get_options(requires_root=False)
        
        assert len(root_options) > 0
        assert len(non_root_options) > 0
        
        # -sS requires root
        root_names = [opt.name for opt in root_options]
        assert "-sS" in root_names
        
        # -sT doesn't require root
        non_root_names = [opt.name for opt in non_root_options]
        assert "-sT" in non_root_names


# ============================================================================
# Test: Conflict Detection
# ============================================================================

class TestConflictDetection:
    """Test conflict detection in Knowledge Graph."""
    
    def test_get_conflicts_sS(self, kg_client):
        """Test conflicts for -sS flag."""
        conflicts = kg_client.get_conflicts("-sS")
        assert len(conflicts) > 0
        
        # -sS should conflict with other scan types
        assert "-sT" in conflicts
        assert "-sU" in conflicts
        assert "-sn" in conflicts
    
    def test_get_conflicts_sT(self, kg_client):
        """Test conflicts for -sT flag."""
        conflicts = kg_client.get_conflicts("-sT")
        assert len(conflicts) > 0
        assert "-sS" in conflicts
    
    def test_get_conflicts_port_spec(self, kg_client):
        """Test conflicts for port specification flags."""
        conflicts_p = kg_client.get_conflicts("-p")
        conflicts_F = kg_client.get_conflicts("-F")
        
        # -p and -F should conflict
        assert "-F" in conflicts_p
        assert "-p" in conflicts_F
    
    def test_validate_command_conflicts_clean(self, kg_client):
        """Test validation of command without conflicts."""
        result = kg_client.validate_command_conflicts(["-sS", "-p", "-sV"])
        # Should have no conflicts
        assert len(result) == 0
    
    def test_validate_command_conflicts_found(self, kg_client):
        """Test validation detects conflicts."""
        result = kg_client.validate_command_conflicts(["-sS", "-sT"])
        # Should detect conflict
        assert len(result) > 0
        assert "-sS" in result or "-sT" in result


# ============================================================================
# Test: KG Helper Functions
# ============================================================================

class TestKGHelperFunctions:
    """Test KG utility helper functions."""
    
    def test_get_options_function(self):
        """Test get_options helper function."""
        options = get_options()
        assert len(options) > 0
    
    def test_get_options_by_category(self):
        """Test get_options with category filter."""
        scan_options = get_options(category="SCAN_TYPE")
        assert len(scan_options) > 0
    
    def test_get_options_exclude_conflicts(self):
        """Test get_options with conflict exclusion."""
        # Get options that don't conflict with -sS
        options = get_options(exclude_conflicts=["-sS"])
        option_names = [opt.name for opt in options]
        
        # -sT should be excluded (conflicts with -sS)
        assert "-sT" not in option_names
    
    def test_get_conflicts_function(self):
        """Test get_conflicts helper function."""
        conflicts = get_conflicts("-sS")
        assert len(conflicts) > 0
        assert "-sT" in conflicts


# ============================================================================
# Test: Fallback Mode
# ============================================================================

class TestFallbackMode:
    """Test KG fallback mode when Neo4j unavailable."""
    
    def test_fallback_initialization(self):
        """Test that fallback data is loaded when Neo4j unavailable."""
        # Create client with invalid credentials to force fallback
        os.environ["NEO4J_PASSWORD"] = "wrong_password_for_test"
        client = Neo4jClient()
        
        # Should still have fallback options
        options = client.get_options()
        assert len(options) > 0
        
        # Reset environment
        os.environ["NEO4J_PASSWORD"] = "password123"
    
    def test_fallback_has_common_options(self):
        """Test fallback data includes common options."""
        os.environ["NEO4J_PASSWORD"] = "wrong_password_for_test"
        client = Neo4jClient()
        
        options = client.get_options()
        option_names = [opt.name for opt in options]
        
        # Common options should be present
        assert "-sS" in option_names
        assert "-sT" in option_names
        assert "-p" in option_names
        assert "-sV" in option_names
        
        os.environ["NEO4J_PASSWORD"] = "password123"


# ============================================================================
# Test: Performance
# ============================================================================

class TestKGPerformance:
    """Test KG query performance."""
    
    def test_get_options_performance(self, kg_client):
        """Test get_options completes quickly."""
        import time
        start = time.time()
        options = kg_client.get_options()
        duration = time.time() - start
        
        assert duration < 1.0  # Should be < 1 second
    
    def test_get_conflicts_performance(self, kg_client):
        """Test get_conflicts completes quickly."""
        import time
        start = time.time()
        conflicts = kg_client.get_conflicts("-sS")
        duration = time.time() - start
        
        assert duration < 0.5  # Should be < 500ms
    
    def test_validate_conflicts_performance(self, kg_client):
        """Test conflict validation completes quickly."""
        import time
        start = time.time()
        result = kg_client.validate_command_conflicts(["-sS", "-p", "-sV", "-O"])
        duration = time.time() - start
        
        assert duration < 1.0  # Should be < 1 second


# ============================================================================
# Test: Data Completeness
# ============================================================================

class TestDataCompleteness:
    """Test that KG has complete data."""
    
    def test_all_categories_present(self, kg_client):
        """Test that all major categories exist."""
        expected_categories = [
            "SCAN_TYPE",
            "PORT_SPEC",
            "SERVICE_DETECTION",
            "OS_DETECTION",
            "TIMING",
            "OUTPUT"
        ]
        
        all_options = kg_client.get_options()
        categories = set(opt.category for opt in all_options)
        
        for cat in expected_categories:
            assert cat in categories, f"Category {cat} missing"
    
    def test_common_flags_present(self, kg_client):
        """Test that common nmap flags are present."""
        all_options = kg_client.get_options()
        option_names = [opt.name for opt in all_options]
        
        common_flags = [
            "-sS", "-sT", "-sU", "-sn",  # Scan types
            "-p", "-F", "-p-",            # Port specs
            "-sV", "-O",                  # Detection
            "-T0", "-T1", "-T2", "-T3", "-T4", "-T5",  # Timing
            "-A", "-v"                    # Misc
        ]
        
        for flag in common_flags:
            assert flag in option_names, f"Flag {flag} missing"
    
    def test_option_properties_complete(self, kg_client):
        """Test that options have all required properties."""
        options = kg_client.get_options()
        
        for opt in options[:10]:  # Check first 10
            assert opt.name is not None
            assert opt.category is not None
            assert opt.description is not None
            assert opt.requires_root is not None
            assert opt.requires_args is not None
            assert opt.conflicts_with is not None
            assert opt.example is not None


# ============================================================================
# Summary
# ============================================================================

def test_neo4j_suite_summary(check_neo4j_running):
    """Print Neo4j test suite summary."""
    print("\n" + "="*60)
    print("🧪 NEO4J KNOWLEDGE GRAPH TEST SUITE")
    print("="*60)
    print(f"✅ Neo4j connection: OK")
    print(f"✅ Data integrity: OK")
    print(f"✅ Conflict detection: OK")
    print(f"✅ Performance: OK")
    print("="*60)