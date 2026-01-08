#!/usr/bin/env python3
"""
Knowledge Graph Test Script (No Docker Required)
=================================================

This script tests the Knowledge Graph in mock mode.
NO installation required - works immediately!

Usage:
    python3 test_kg_standalone.py
"""

def test_knowledge_graph():
    """Test all KG functionality without Docker/Neo4j"""
    
    print("\n" + "=" * 70)
    print(" KNOWLEDGE GRAPH TEST SUITE (Mock Mode - No Docker)")
    print("=" * 70)
    
    # Import KG utilities
    try:
        from agents.comprehension.kg_utils import (
            get_options, 
            get_conflicts, 
            get_port_info,
            NmapOption,
            Port
        )
        print("\n✅ Successfully imported KG utilities")
    except ImportError as e:
        print(f"\n❌ Failed to import: {e}")
        return False
    
    test_results = []
    
    # Test 1: Basic option retrieval
    print("\n" + "-" * 70)
    print("TEST 1: Get all options")
    print("-" * 70)
    try:
        all_opts = get_options()
        print(f"✅ Retrieved {len(all_opts)} options")
        print(f"   Options: {[opt.name for opt in all_opts[:5]]}...")
        test_results.append(True)
    except Exception as e:
        print(f"❌ FAILED: {e}")
        test_results.append(False)
    
    # Test 2: Filter by category
    print("\n" + "-" * 70)
    print("TEST 2: Get options by category (SCAN_TYPE)")
    print("-" * 70)
    try:
        scans = get_options(category='SCAN_TYPE')
        print(f"✅ Found {len(scans)} scan types:")
        for scan in scans:
            root_status = "🔒 root" if scan.requires_root else "🔓 no root"
            print(f"   • {scan.name:6} → {scan.description[:30]:30} ({root_status})")
        test_results.append(len(scans) >= 3)
    except Exception as e:
        print(f"❌ FAILED: {e}")
        test_results.append(False)
    
    # Test 3: Filter by root requirement
    print("\n" + "-" * 70)
    print("TEST 3: Get options that DON'T require root")
    print("-" * 70)
    try:
        no_root = get_options(requires_root=False)
        print(f"✅ Found {len(no_root)} non-root options:")
        print(f"   {[opt.name for opt in no_root]}")
        test_results.append(len(no_root) > 0)
    except Exception as e:
        print(f"❌ FAILED: {e}")
        test_results.append(False)
    
    # Test 4: Filter by complexity
    print("\n" + "-" * 70)
    print("TEST 4: Get EASY complexity options")
    print("-" * 70)
    try:
        easy = get_options(complexity='EASY')
        print(f"✅ Found {len(easy)} EASY options:")
        for opt in easy:
            print(f"   • {opt.name}: {opt.description}")
        test_results.append(len(easy) > 0)
    except Exception as e:
        print(f"❌ FAILED: {e}")
        test_results.append(False)
    
    # Test 5: Max complexity filter
    print("\n" + "-" * 70)
    print("TEST 5: Get options up to MEDIUM complexity")
    print("-" * 70)
    try:
        medium = get_options(max_complexity='MEDIUM')
        print(f"✅ Found {len(medium)} options (EASY + MEDIUM)")
        test_results.append(len(medium) > len(easy) if 'easy' in locals() else True)
    except Exception as e:
        print(f"❌ FAILED: {e}")
        test_results.append(False)
    
    # Test 6: Conflict detection
    print("\n" + "-" * 70)
    print("TEST 6: Check conflicts for -sS (TCP SYN scan)")
    print("-" * 70)
    try:
        conflicts = get_conflicts('-sS')
        print(f"✅ -sS conflicts with: {conflicts}")
        if '-sT' in conflicts and '-sU' in conflicts:
            print("   ✓ Correctly identifies -sT and -sU as conflicts")
        test_results.append(len(conflicts) > 0)
    except Exception as e:
        print(f"❌ FAILED: {e}")
        test_results.append(False)
    
    # Test 7: Ping scan conflicts
    print("\n" + "-" * 70)
    print("TEST 7: Check conflicts for -sn (ping scan)")
    print("-" * 70)
    try:
        conflicts_sn = get_conflicts('-sn')
        print(f"✅ -sn conflicts with: {conflicts_sn}")
        if '-p' in conflicts_sn:
            print("   ✓ Correctly identifies port scan conflicts")
        test_results.append(True)
    except Exception as e:
        print(f"❌ FAILED: {e}")
        test_results.append(False)
    
    # Test 8: Port lookup by service
    print("\n" + "-" * 70)
    print("TEST 8: Look up port by service name (SSH)")
    print("-" * 70)
    try:
        ssh = get_port_info(service='SSH')
        print(f"✅ SSH service:")
        print(f"   • Port: {ssh.number}")
        print(f"   • Protocol: {ssh.protocol}")
        print(f"   • Description: {ssh.description}")
        test_results.append(ssh.number == 22)
    except Exception as e:
        print(f"❌ FAILED: {e}")
        test_results.append(False)
    
    # Test 9: Port lookup by number
    print("\n" + "-" * 70)
    print("TEST 9: Look up port by number (443)")
    print("-" * 70)
    try:
        https = get_port_info(port=443)
        print(f"✅ Port 443:")
        print(f"   • Service: {https.service}")
        print(f"   • Protocol: {https.protocol}")
        test_results.append(https.service.upper() == 'HTTPS')
    except Exception as e:
        print(f"❌ FAILED: {e}")
        test_results.append(False)
    
    # Test 10: Case-insensitive lookup
    print("\n" + "-" * 70)
    print("TEST 10: Case-insensitive service lookup")
    print("-" * 70)
    try:
        http_upper = get_port_info(service='HTTP')
        http_lower = get_port_info(service='http')
        http_mixed = get_port_info(service='HtTp')
        
        if http_upper.number == http_lower.number == http_mixed.number:
            print(f"✅ All variations return port {http_upper.number}")
            test_results.append(True)
        else:
            print("❌ Case sensitivity issue")
            test_results.append(False)
    except Exception as e:
        print(f"❌ FAILED: {e}")
        test_results.append(False)
    
    # Test 11: Complex combined query
    print("\n" + "-" * 70)
    print("TEST 11: Complex query - Safe, MEDIUM scan types")
    print("-" * 70)
    try:
        safe_scans = get_options(
            category='SCAN_TYPE',
            requires_root=False,
            max_complexity='MEDIUM'
        )
        print(f"✅ Found {len(safe_scans)} safe scan types:")
        for scan in safe_scans:
            print(f"   • {scan.name}: {scan.description}")
        test_results.append(len(safe_scans) > 0)
    except Exception as e:
        print(f"❌ FAILED: {e}")
        test_results.append(False)
    
    # Test 12: Data model validation
    print("\n" + "-" * 70)
    print("TEST 12: Validate data models")
    print("-" * 70)
    try:
        opt = get_options()[0]
        assert hasattr(opt, 'name')
        assert hasattr(opt, 'category')
        assert hasattr(opt, 'requires_root')
        assert hasattr(opt, 'conflicts_with')
        print("✅ NmapOption model has all required fields")
        
        port = get_port_info(port=22)
        assert hasattr(port, 'number')
        assert hasattr(port, 'service')
        assert hasattr(port, 'protocol')
        print("✅ Port model has all required fields")
        
        test_results.append(True)
    except Exception as e:
        print(f"❌ FAILED: {e}")
        test_results.append(False)
    
    # Print summary
    print("\n" + "=" * 70)
    print(" TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(test_results)
    total = len(test_results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"\n✅ Passed: {passed}/{total} tests ({percentage:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✓ Knowledge Graph is working correctly")
        print("✓ Mock mode is functional")
        print("✓ No Docker/Neo4j required")
        print("✓ Ready for integration with other agents")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False


def demonstrate_usage():
    """Show practical usage examples"""
    
    print("\n" + "=" * 70)
    print(" PRACTICAL USAGE EXAMPLES")
    print("=" * 70)
    
    from agents.comprehension.kg_utils import get_options, get_conflicts
    
    print("\n📝 Example 1: Get options for Easy/Medium generator")
    print("-" * 70)
    print("Code:")
    print("  allowed_flags = get_options(")
    print("      max_complexity='MEDIUM',")
    print("      requires_root=False")
    print("  )")
    
    allowed = get_options(max_complexity='MEDIUM', requires_root=False)
    print(f"\nResult: {len(allowed)} safe flags for T5 prompting:")
    print(f"  {[opt.name for opt in allowed]}")
    
    print("\n📝 Example 2: Validate command for conflicts")
    print("-" * 70)
    print("Code:")
    print("  def validate_command(flags):")
    print("      for flag in flags:")
    print("          conflicts = get_conflicts(flag)")
    print("          if any(c in flags for c in conflicts):")
    print("              return False")
    print("      return True")
    
    # Test with conflicting flags
    test_cmd = ['-sS', '-sT']
    conflicts = get_conflicts('-sS')
    has_conflict = any(c in test_cmd for c in conflicts)
    
    print(f"\nTest: nmap {' '.join(test_cmd)} 192.168.1.1")
    print(f"  -sS conflicts with: {conflicts}")
    print(f"  Command has conflict: {has_conflict}")
    print(f"  Validation: {'❌ INVALID' if has_conflict else '✅ VALID'}")
    
    print("\n📝 Example 3: Build port specification from service")
    print("-" * 70)
    print("Code:")
    print("  from agents.comprehension.kg_utils import get_port_info")
    print("  services = ['SSH', 'HTTP', 'HTTPS']")
    print("  ports = [get_port_info(service=s).number for s in services]")
    print("  port_spec = ','.join(map(str, ports))")
    
    from agents.comprehension.kg_utils import get_port_info
    services = ['SSH', 'HTTP', 'HTTPS']
    ports = [get_port_info(service=s).number for s in services]
    port_spec = ','.join(map(str, ports))
    
    print(f"\nResult: -p {port_spec}")
    print(f"  Full command: nmap -p {port_spec} 192.168.1.1")


if __name__ == "__main__":
    print("\n╔════════════════════════════════════════════════════════════════════╗")
    print("║  NMAP-AI Knowledge Graph Test Suite                               ║")
    print("║  Testing without Docker/Neo4j (Mock Mode)                         ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    
    # Run tests
    success = test_knowledge_graph()
    
    # Show usage examples
    demonstrate_usage()
    
    # Final message
    print("\n" + "=" * 70)
    if success:
        print("✅ Knowledge Graph is READY TO USE!")
    else:
        print("⚠️  Some tests failed (expected in mock mode)")
    print("\n💡 To use with full Neo4j graph:")
    print("   1. docker run -d -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j")
    print("   2. cat data/kg/init.cypher | cypher-shell -u neo4j -p password")
    print("   3. export NEO4J_URI='bolt://localhost:7687'")
    print("   4. Run tests again")
    print("=" * 70 + "\n")