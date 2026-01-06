"""
Integration Tests for Neo4j Knowledge Graph
Tests REAL Neo4j functionality, not just fallback

Run: pytest tests/test_neo4j_integration.py -v
"""

import pytest
from agents.comprehension.kg_utils import get_kg_client, Neo4jClient
from agents.validator.conflict_checker import validate_conflicts, check_requires_root


class TestNeo4jConnection:
    """Test Neo4j connection and availability"""
    
    def test_neo4j_is_available(self):
        """Test that Neo4j is running and accessible"""
        kg = get_kg_client()
        
        # Neo4j should be connected (not using fallback)
        assert kg.driver is not None, "Neo4j driver should be connected (not in fallback mode)"
        
        print("\n✅ Neo4j is UP and connected!")
    
    def test_neo4j_has_data(self):
        """Test that Neo4j contains nmap options"""
        kg = get_kg_client()
        
        # Should have data
        options = kg.get_options()
        
        assert len(options) > 0, "Neo4j should contain nmap options"
        assert len(options) >= 20, f"Expected at least 20 options, got {len(options)}"
        
        print(f"\n✅ Neo4j has {len(options)} options")
    
    def test_neo4j_has_conflicts(self):
        """Test that Neo4j contains conflict relationships"""
        kg = get_kg_client()
        
        # Test known conflict
        conflicts = kg.get_conflicts('-sS')
        
        assert len(conflicts) > 0, "Neo4j should have conflict data for -sS"
        assert '-sT' in conflicts, "-sS should conflict with -sT"
        
        print(f"\n✅ Neo4j has conflict data: -sS conflicts with {conflicts}")


class TestNeo4jVsFallback:
    """Compare Neo4j vs Fallback to ensure they behave correctly"""
    
    def test_fallback_vs_neo4j_same_results(self):
        """Test that Neo4j and fallback give consistent results"""
        kg = get_kg_client()
        
        # If Neo4j is available, compare with fallback
        if kg.driver:
            # Get conflicts from Neo4j
            neo4j_conflicts = set(kg.get_conflicts('-sS'))
            
            # Get conflicts from fallback (by forcing it)
            kg_fallback = Neo4jClient()
            kg_fallback.driver = None  # Force fallback
            kg_fallback._init_fallback_data()
            fallback_conflicts = set(kg_fallback.get_conflicts('-sS'))
            
            # Compare
            print(f"\nNeo4j conflicts: {neo4j_conflicts}")
            print(f"Fallback conflicts: {fallback_conflicts}")
            
            # They should have significant overlap
            overlap = neo4j_conflicts & fallback_conflicts
            assert len(overlap) >= 3, "Neo4j and fallback should have similar conflict data"
            
            print(f"✅ Overlap: {len(overlap)}/{max(len(neo4j_conflicts), len(fallback_conflicts))} conflicts")


class TestConflictDetectionWithNeo4j:
    """Test conflict detection using REAL Neo4j (not fallback)"""
    
    def test_scan_type_conflict_with_neo4j(self, neo4j_client):
        """Test scan type conflict detection using Neo4j"""
        kg = neo4j_client
        
        # Ensure we're using Neo4j
        assert kg.driver is not None, "This test requires Neo4j to be running"
        
        # Test conflict
        valid, msg = validate_conflicts("nmap -sS -sT 192.168.1.1", kg_client=kg)
        
        assert valid == False, "Should detect conflict between -sS and -sT"
        assert "-sS" in msg and "-sT" in msg, "Error message should mention both flags"
        
        print(f"\n✅ Neo4j detected conflict: {msg}")
    
    def test_ping_scan_port_conflict_with_neo4j(self, neo4j_client):
        """Test -sn vs -p conflict using Neo4j"""
        kg = neo4j_client
        
        assert kg.driver is not None, "This test requires Neo4j"
        
        valid, msg = validate_conflicts("nmap -sn -p 80 192.168.1.1", kg_client=kg)
        
        assert valid == False, "Should detect conflict between -sn and -p"
        assert "-sn" in msg and "-p" in msg, "Error message should mention both flags"
        
        print(f"\n✅ Neo4j detected conflict: {msg}")
    
    def test_no_conflict_with_neo4j(self, neo4j_client):
        """Test that valid commands pass with Neo4j"""
        kg = neo4j_client
        
        assert kg.driver is not None, "This test requires Neo4j"
        
        valid, msg = validate_conflicts("nmap -sV -p 80,443 192.168.1.1", kg_client=kg)
        
        assert valid == True, "Should not detect conflict in valid command"
        
        print(f"\n✅ Neo4j validated command: {msg}")


class TestRootDetectionWithNeo4j:
    """Test root requirement detection using REAL Neo4j"""
    
    def test_root_required_with_neo4j(self, neo4j_client):
        """Test that -sS is detected as requiring root via Neo4j"""
        kg = neo4j_client
        
        assert kg.driver is not None, "This test requires Neo4j"
        
        requires_root, flags = check_requires_root("nmap -sS 192.168.1.1", kg_client=kg)
        
        assert requires_root == True, "-sS should require root"
        assert '-sS' in flags, "-sS should be in the list of root-required flags"
        
        print(f"\n✅ Neo4j detected root requirement: {flags}")
    
    def test_no_root_required_with_neo4j(self, neo4j_client):
        """Test that -sT does not require root via Neo4j"""
        kg = neo4j_client
        
        assert kg.driver is not None, "This test requires Neo4j"
        
        requires_root, flags = check_requires_root("nmap -sT 192.168.1.1", kg_client=kg)
        
        assert requires_root == False, "-sT should not require root"
        assert len(flags) == 0, "Should not have any root-required flags"
        
        print(f"\n✅ Neo4j validated no root needed")
    
    def test_multiple_root_flags_with_neo4j(self, neo4j_client):
        """Test detection of multiple root-required flags"""
        kg = neo4j_client
        
        assert kg.driver is not None, "This test requires Neo4j"
        
        requires_root, flags = check_requires_root("nmap -sS -O 192.168.1.1", kg_client=kg)
        
        assert requires_root == True, "Should require root"
        assert '-sS' in flags, "-sS should require root"
        assert '-O' in flags, "-O should require root"
        
        print(f"\n✅ Neo4j detected multiple root flags: {flags}")


class TestNeo4jPerformance:
    """Test that Neo4j performs well"""
    
    def test_query_performance(self):
        """Test that Neo4j queries are fast"""
        import time
        
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        # Time multiple queries
        start = time.time()
        for _ in range(10):
            kg.get_conflicts('-sS')
            kg.get_options(requires_root=True)
        end = time.time()
        
        avg_time = (end - start) / 10
        
        assert avg_time < 0.5, f"Queries should be fast, got {avg_time:.3f}s average"
        
        print(f"\n✅ Neo4j query performance: {avg_time*1000:.1f}ms average")


class TestNeo4jDataQuality:
    """Test that Neo4j has quality data"""
    
    def test_all_scan_types_present(self):
        """Test that all major scan types are in Neo4j"""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        # Get scan type options
        scan_options = kg.get_options(category="SCAN_TYPE")
        scan_names = [opt.name for opt in scan_options]
        
        required_scans = ['-sS', '-sT', '-sU', '-sN', '-sF', '-sX']
        
        for scan in required_scans:
            assert scan in scan_names, f"{scan} should be in Neo4j"
        
        print(f"\n✅ All scan types present: {scan_names}")
    
    def test_bidirectional_conflicts(self):
        """Test that conflicts are bidirectional"""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        # If -sS conflicts with -sT, then -sT should conflict with -sS
        ss_conflicts = kg.get_conflicts('-sS')
        st_conflicts = kg.get_conflicts('-sT')
        
        if '-sT' in ss_conflicts:
            assert '-sS' in st_conflicts, "Conflicts should be bidirectional"
        
        print(f"\n✅ Conflicts are bidirectional")
    
    def test_root_flags_accuracy(self):
        """Test that root flags are accurate"""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        # Get root-required options
        root_options = kg.get_options(requires_root=True)
        root_names = [opt.name for opt in root_options]
        
        # These should require root
        should_require_root = ['-sS', '-sU', '-O']
        for flag in should_require_root:
            assert flag in root_names, f"{flag} should require root"
        
        # -sT should NOT require root
        assert '-sT' not in root_names, "-sT should not require root"
        
        print(f"\n✅ Root requirements accurate: {root_names}")


# ============================================================================
# SUMMARY REPORT
# ============================================================================

def pytest_sessionfinish(session, exitstatus):
    """Print summary after all tests"""
    if exitstatus == 0:
        print("\n" + "="*70)
        print("✅✅✅ ALL NEO4J INTEGRATION TESTS PASSED! ✅✅✅")
        print("="*70)
        print("\n🎉 Neo4j is properly integrated with Person 4's validator!")
        print("\n📊 Integration verified:")
        print("   ✅ Neo4j connection working")
        print("   ✅ Data populated correctly")
        print("   ✅ Conflict detection accurate")
        print("   ✅ Root detection accurate")
        print("   ✅ Performance acceptable")
        print("   ✅ Data quality verified")
        print("\n" + "="*70)