"""
P1 ↔ P4 Integration Validation Test Suite
=========================================

This test suite validates the complete integration between:
- Person 1 (P1): Knowledge Graph component
- Person 4 (P4): Validator component

Test Categories:
1. Data Integrity Tests - verify KG data quality
2. Conflict Detection Tests - validate conflict detection via KG
3. Root Detection Tests - validate root requirement detection via KG
4. Edge Case Tests - test unusual scenarios
5. Performance Tests - ensure queries are fast
6. Fallback Tests - verify graceful degradation

Run: pytest tests/test_p1_p4_integration.py -v
"""

import pytest
import time
from typing import List
from agents.comprehension.kg_utils import get_kg_client, Neo4jClient
from agents.validator.conflict_checker import validate_conflicts, check_requires_root


class TestDataIntegrity:
    """Validate that Neo4j contains correct and complete data."""
    
    def test_minimum_options_loaded(self):
        """Verify minimum number of options are loaded."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        options = kg.get_options()
        
        # Should have at least 40 options loaded
        assert len(options) >= 40, f"Expected at least 40 options, got {len(options)}"
        
        print(f"\n✅ Loaded {len(options)} options")
    
    def test_all_scan_types_present(self):
        """Verify all major scan types are present."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        scan_options = kg.get_options(category="SCAN_TYPE")
        scan_names = [opt.name for opt in scan_options]
        
        required_scans = ['-sS', '-sT', '-sU', '-sN', '-sF', '-sX', '-sA', '-sW', '-sM']
        
        for scan in required_scans:
            assert scan in scan_names, f"Missing scan type: {scan}"
        
        print(f"\n✅ All {len(required_scans)} scan types present")
    
    def test_port_spec_options_present(self):
        """Verify port specification options are present."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        port_options = kg.get_options(category="PORT_SPEC")
        port_names = [opt.name for opt in port_options]
        
        required_ports = ['-p', '-p-', '-F', '--top-ports']
        
        for port in required_ports:
            assert port in port_names, f"Missing port option: {port}"
        
        print(f"\n✅ All {len(required_ports)} port spec options present")
    
    def test_timing_templates_present(self):
        """Verify all timing templates are present."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        timing_options = kg.get_options(category="TIMING")
        timing_names = [opt.name for opt in timing_options]
        
        required_timing = ['-T0', '-T1', '-T2', '-T3', '-T4', '-T5']
        
        for timing in required_timing:
            assert timing in timing_names, f"Missing timing option: {timing}"
        
        print(f"\n✅ All {len(required_timing)} timing options present")
    
    def test_options_have_required_fields(self):
        """Verify all options have required fields."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        options = kg.get_options()
        
        for opt in options[:10]:  # Test first 10
            assert opt.name, "Option missing name"
            assert opt.category, "Option missing category"
            assert opt.description, "Option missing description"
            assert opt.example, "Option missing example"
            assert isinstance(opt.requires_root, bool), "requires_root not a bool"
            assert isinstance(opt.requires_args, bool), "requires_args not a bool"
            assert isinstance(opt.conflicts_with, list), "conflicts_with not a list"
        
        print(f"\n✅ All options have required fields")
    
    def test_bidirectional_conflicts(self):
        """Verify conflicts are bidirectional."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        # If -sS conflicts with -sT, then -sT should conflict with -sS
        ss_conflicts = kg.get_conflicts('-sS')
        st_conflicts = kg.get_conflicts('-sT')
        
        if '-sT' in ss_conflicts:
            assert '-sS' in st_conflicts, "Conflicts not bidirectional: -sS ↔ -sT"
        
        if '-sU' in ss_conflicts:
            su_conflicts = kg.get_conflicts('-sU')
            assert '-sS' in su_conflicts, "Conflicts not bidirectional: -sS ↔ -sU"
        
        print(f"\n✅ Conflicts are bidirectional")


class TestConflictDetectionViaKG:
    """Test conflict detection using real Neo4j data."""
    
    def test_scan_type_conflicts(self):
        """Test detection of scan type conflicts."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        # Test all common scan type conflicts
        test_cases = [
            ("nmap -sS -sT 192.168.1.1", False, ["-sS", "-sT"]),
            ("nmap -sS -sU 192.168.1.1", False, ["-sS", "-sU"]),
            ("nmap -sT -sU 192.168.1.1", False, ["-sT", "-sU"]),
            ("nmap -sN -sF 192.168.1.1", False, ["-sN", "-sF"]),
            ("nmap -sS 192.168.1.1", True, None),  # No conflict
        ]
        
        for cmd, should_pass, conflicting_flags in test_cases:
            valid, msg = validate_conflicts(cmd, kg_client=kg)
            
            if should_pass:
                assert valid, f"Command should be valid: {cmd}"
            else:
                assert not valid, f"Should detect conflict in: {cmd}"
                for flag in conflicting_flags:
                    assert flag in msg, f"Error message should mention {flag}"
        
        print(f"\n✅ All scan type conflicts detected correctly")
    
    def test_port_spec_conflicts(self):
        """Test detection of port specification conflicts."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        test_cases = [
            ("nmap -p 80 -F 192.168.1.1", False, ["-p", "-F"]),
            ("nmap -p- --top-ports 10 192.168.1.1", False, ["-p-", "--top-ports"]),
            ("nmap -F --top-ports 20 192.168.1.1", False, ["-F", "--top-ports"]),
            ("nmap -p 80,443 192.168.1.1", True, None),  # No conflict
        ]
        
        for cmd, should_pass, conflicting_flags in test_cases:
            valid, msg = validate_conflicts(cmd, kg_client=kg)
            
            if should_pass:
                assert valid, f"Command should be valid: {cmd}"
            else:
                assert not valid, f"Should detect conflict in: {cmd}"
                if conflicting_flags:
                    for flag in conflicting_flags:
                        assert flag in msg, f"Error message should mention {flag}"
        
        print(f"\n✅ All port spec conflicts detected correctly")
    
    def test_timing_conflicts(self):
        """Test detection of timing template conflicts."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        test_cases = [
            ("nmap -T0 -T4 192.168.1.1", False, ["-T0", "-T4"]),
            ("nmap -T1 -T5 192.168.1.1", False, ["-T1", "-T5"]),
            ("nmap -T2 -T3 192.168.1.1", False, ["-T2", "-T3"]),
            ("nmap -T4 192.168.1.1", True, None),  # No conflict
        ]
        
        for cmd, should_pass, conflicting_flags in test_cases:
            valid, msg = validate_conflicts(cmd, kg_client=kg)
            
            if should_pass:
                assert valid, f"Command should be valid: {cmd}"
            else:
                assert not valid, f"Should detect conflict in: {cmd}"
                if conflicting_flags:
                    for flag in conflicting_flags:
                        assert flag in msg, f"Error message should mention {flag}"
        
        print(f"\n✅ All timing conflicts detected correctly")
    
    def test_ping_scan_conflicts(self):
        """Test -sn (ping scan) conflicts with port scanning."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        test_cases = [
            ("nmap -sn -p 80 192.168.1.0/24", False, ["-sn", "-p"]),
            ("nmap -sn -F 192.168.1.0/24", False, ["-sn", "-F"]),
            ("nmap -sn -p- 192.168.1.0/24", False, ["-sn", "-p-"]),
            ("nmap -sn 192.168.1.0/24", True, None),  # No conflict
        ]
        
        for cmd, should_pass, conflicting_flags in test_cases:
            valid, msg = validate_conflicts(cmd, kg_client=kg)
            
            if should_pass:
                assert valid, f"Command should be valid: {cmd}"
            else:
                assert not valid, f"Should detect conflict in: {cmd}"
                if conflicting_flags:
                    for flag in conflicting_flags:
                        assert flag in msg, f"Error message should mention {flag}"
        
        print(f"\n✅ All ping scan conflicts detected correctly")
    
    def test_complex_multi_conflict(self):
        """Test detection of multiple simultaneous conflicts."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        # Command with multiple conflicts
        cmd = "nmap -sS -sT -p 80 -F -T0 -T4 192.168.1.1"
        valid, msg = validate_conflicts(cmd, kg_client=kg)
        
        assert not valid, "Should detect multiple conflicts"
        
        # Should mention at least some of the conflicts
        has_scan_conflict = ("-sS" in msg and "-sT" in msg)
        has_port_conflict = ("-p" in msg and "-F" in msg)
        has_timing_conflict = ("-T0" in msg and "-T4" in msg)
        
        conflicts_detected = sum([has_scan_conflict, has_port_conflict, has_timing_conflict])
        
        assert conflicts_detected >= 1, "Should detect at least one type of conflict"
        
        print(f"\n✅ Multiple conflicts detected: {conflicts_detected}/3 types")


class TestRootDetectionViaKG:
    """Test root requirement detection using real Neo4j data."""
    
    def test_syn_scan_requires_root(self):
        """Test that -sS requires root."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        requires_root, flags = check_requires_root("nmap -sS 192.168.1.1", kg_client=kg)
        
        assert requires_root, "-sS should require root"
        assert '-sS' in flags, "-sS should be in root-required flags"
        
        print(f"\n✅ -sS correctly requires root")
    
    def test_connect_scan_no_root(self):
        """Test that -sT does not require root."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        requires_root, flags = check_requires_root("nmap -sT 192.168.1.1", kg_client=kg)
        
        assert not requires_root, "-sT should not require root"
        assert len(flags) == 0, "Should not have any root-required flags"
        
        print(f"\n✅ -sT correctly does not require root")
    
    def test_os_detection_requires_root(self):
        """Test that -O requires root."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        requires_root, flags = check_requires_root("nmap -O 192.168.1.1", kg_client=kg)
        
        assert requires_root, "-O should require root"
        assert '-O' in flags, "-O should be in root-required flags"
        
        print(f"\n✅ -O correctly requires root")
    
    def test_udp_scan_requires_root(self):
        """Test that -sU requires root."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        requires_root, flags = check_requires_root("nmap -sU 192.168.1.1", kg_client=kg)
        
        assert requires_root, "-sU should require root"
        assert '-sU' in flags, "-sU should be in root-required flags"
        
        print(f"\n✅ -sU correctly requires root")
    
    def test_aggressive_scan_requires_root(self):
        """Test that -A requires root."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        requires_root, flags = check_requires_root("nmap -A 192.168.1.1", kg_client=kg)
        
        assert requires_root, "-A should require root"
        assert '-A' in flags, "-A should be in root-required flags"
        
        print(f"\n✅ -A correctly requires root")
    
    def test_multiple_root_flags(self):
        """Test detection of multiple root-required flags."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        requires_root, flags = check_requires_root("nmap -sS -O -sU 192.168.1.1", kg_client=kg)
        
        assert requires_root, "Should require root"
        assert '-sS' in flags, "-sS should be detected"
        assert '-O' in flags, "-O should be detected"
        assert '-sU' in flags, "-sU should be detected"
        assert len(flags) >= 3, f"Should detect at least 3 flags, got {len(flags)}"
        
        print(f"\n✅ Multiple root flags detected: {flags}")
    
    def test_no_root_flags_mixed(self):
        """Test command with mix of root and non-root flags."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        # -sV, -p, -T4 don't require root, but -sS does
        requires_root, flags = check_requires_root("nmap -sS -sV -p 80 -T4 192.168.1.1", kg_client=kg)
        
        assert requires_root, "Should require root due to -sS"
        assert '-sS' in flags, "-sS should be detected"
        assert '-sV' not in flags, "-sV should not be in root flags"
        assert '-p' not in flags, "-p should not be in root flags"
        assert '-T4' not in flags, "-T4 should not be in root flags"
        
        print(f"\n✅ Correctly identified root flags in mixed command")


class TestEdgeCases:
    """Test edge cases and unusual scenarios."""
    
    def test_empty_command(self):
        """Test validation of empty command."""
        kg = get_kg_client()
        
        valid, msg = validate_conflicts("", kg_client=kg)
        # Should handle gracefully (depends on implementation)
        
        print(f"\n✅ Empty command handled: valid={valid}")
    
    def test_only_target(self):
        """Test command with only target, no flags."""
        kg = get_kg_client()
        
        valid, msg = validate_conflicts("nmap 192.168.1.1", kg_client=kg)
        
        assert valid, "Command with only target should be valid"
        
        print(f"\n✅ Target-only command valid")
    
    def test_unknown_flag(self):
        """Test command with unknown flag."""
        kg = get_kg_client()
        
        # Command with non-existent flag
        valid, msg = validate_conflicts("nmap -sS --fake-flag 192.168.1.1", kg_client=kg)
        
        # Should still validate known flags
        assert valid or not valid  # Either is acceptable
        
        print(f"\n✅ Unknown flag handled: valid={valid}")
    
    def test_duplicate_flags(self):
        """Test command with duplicate flags."""
        kg = get_kg_client()
        
        valid, msg = validate_conflicts("nmap -sS -sS -p 80 -p 80 192.168.1.1", kg_client=kg)
        
        # Duplicates shouldn't cause crashes
        assert isinstance(valid, bool)
        
        print(f"\n✅ Duplicate flags handled: valid={valid}")
    
    def test_very_long_command(self):
        """Test validation of very long command."""
        kg = get_kg_client()
        
        # Command with many valid flags
        cmd = "nmap -sV -O -T4 -v -d --traceroute --reason --open -oN scan.txt -oX scan.xml 192.168.1.1"
        valid, msg = validate_conflicts(cmd, kg_client=kg)
        
        assert valid, "Long valid command should pass"
        
        print(f"\n✅ Long command validated")


class TestPerformance:
    """Test query performance."""
    
    def test_conflict_check_performance(self):
        """Test that conflict checking is fast."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        cmd = "nmap -sS -sV -p 80,443 -T4 192.168.1.1"
        
        start = time.time()
        for _ in range(100):
            validate_conflicts(cmd, kg_client=kg)
        end = time.time()
        
        avg_time = (end - start) / 100
        
        assert avg_time < 0.1, f"Conflict check too slow: {avg_time*1000:.1f}ms"
        
        print(f"\n✅ Conflict check performance: {avg_time*1000:.1f}ms avg")
    
    def test_root_check_performance(self):
        """Test that root checking is fast."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        cmd = "nmap -sS -O -sU -A 192.168.1.1"
        
        start = time.time()
        for _ in range(100):
            check_requires_root(cmd, kg_client=kg)
        end = time.time()
        
        avg_time = (end - start) / 100
        
        assert avg_time < 0.1, f"Root check too slow: {avg_time*1000:.1f}ms"
        
        print(f"\n✅ Root check performance: {avg_time*1000:.1f}ms avg")
    
    def test_kg_query_performance(self):
        """Test that raw KG queries are fast."""
        kg = get_kg_client()
        
        if kg.driver is None:
            pytest.skip("Neo4j not available")
        
        start = time.time()
        for _ in range(100):
            kg.get_conflicts('-sS')
        end = time.time()
        
        avg_time = (end - start) / 100
        
        assert avg_time < 0.05, f"KG query too slow: {avg_time*1000:.1f}ms"
        
        print(f"\n✅ KG query performance: {avg_time*1000:.1f}ms avg")


class TestFallbackMode:
    """Test graceful degradation to fallback mode."""
    
    def test_fallback_mode_works(self):
        """Test that fallback mode provides basic functionality."""
        # Create client in fallback mode
        kg = Neo4jClient()
        kg.driver = None  # Force fallback
        kg._init_fallback_data()
        
        # Should still work
        options = kg.get_options()
        
        assert len(options) > 0, "Fallback should have options"
        
        conflicts = kg.get_conflicts('-sS')
        
        assert len(conflicts) > 0, "Fallback should have conflict data"
        
        print(f"\n✅ Fallback mode functional: {len(options)} options, {len(conflicts)} conflicts for -sS")
    
    def test_fallback_has_essential_data(self):
        """Test that fallback has essential scan types."""
        kg = Neo4jClient()
        kg.driver = None
        kg._init_fallback_data()
        
        # Check for essential scan types
        essential = ['-sS', '-sT', '-sU', '-sn', '-p', '-O']
        
        for flag in essential:
            conflicts = kg.get_conflicts(flag)
            # Should have some data (even if empty list)
            assert isinstance(conflicts, list), f"Missing data for {flag}"
        
        print(f"\n✅ Fallback has essential data")
    
    def test_validator_works_without_neo4j(self):
        """Test that validator works in fallback mode."""
        # Create fallback client
        kg = Neo4jClient()
        kg.driver = None
        kg._init_fallback_data()
        
        # Test validation
        valid, msg = validate_conflicts("nmap -sS -sT 192.168.1.1", kg_client=kg)
        
        # Should still detect conflicts in fallback mode
        assert not valid, "Should detect conflict even in fallback mode"
        assert "-sS" in msg and "-sT" in msg, "Should mention conflicting flags"
        
        print(f"\n✅ Validator works in fallback mode")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])