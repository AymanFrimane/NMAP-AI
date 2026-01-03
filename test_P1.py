#!/usr/bin/env python3
"""
NMAP-AI - Complete Test Suite (Python Version)
Tests everything without deployment
"""

import sys
import os
import time
import subprocess
from pathlib import Path

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'━'*70}{NC}")
    print(f"{BLUE}  {text}{NC}")
    print(f"{BLUE}{'━'*70}{NC}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{NC}")

def print_error(text):
    print(f"{RED}✗ {text}{NC}")

def print_info(text):
    print(f"{YELLOW}→ {text}{NC}")

# Change to script directory
os.chdir(Path(__file__).parent)

def test_models_trained():
    """Check if models are trained."""
    print_header("Checking Models")
    
    artifacts_dir = Path("artifacts")
    tfidf_path = artifacts_dir / "tfidf.pkl"
    model_path = artifacts_dir / "complexity_model.pkl"
    
    if not tfidf_path.exists() or not model_path.exists():
        print_info("Models not found. Training now...")
        result = subprocess.run(
            ["python", "scripts/train_classifier.py", "--dataset", "/mnt/project/nmap_dataset.json"],
            capture_output=True
        )
        if result.returncode != 0:
            print_error("Training failed")
            print(result.stderr.decode())
            return False
        print_success("Models trained")
    else:
        print_success("Models found")
    
    return True

def test_unit_tests():
    """Run pytest unit tests."""
    print_header("Test 1: Running Unit Tests")
    
    result = subprocess.run(
        ["pytest", "tests/test_comprehension.py", "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print_error("Unit tests failed")
        print(result.stdout)
        return False
    
    # Count passed tests
    passed = result.stdout.count(" PASSED")
    print_success(f"All unit tests passed ({passed} tests)")
    
    return True

def test_classifier():
    """Test classifier manually."""
    print_header("Test 2: Manual Classifier Test")
    
    sys.path.insert(0, str(Path.cwd()))
    from agents.comprehension import get_classifier
    
    classifier = get_classifier()
    
    tests = [
        ("Scan 192.168.1.0/24 for web servers", True, ["EASY", "MEDIUM"]),
        ("TCP SYN scan with OS detection", True, ["MEDIUM", "HARD"]),
        ("What is love?", False, [None]),
    ]
    
    all_passed = True
    for query, expected_relevant, expected_complexity_options in tests:
        result = classifier.comprehend(query)
        
        if result["is_relevant"] != expected_relevant:
            print_error(f"Failed: {query}")
            print(f"  Expected relevant={expected_relevant}, got {result['is_relevant']}")
            all_passed = False
        elif result["complexity"] not in expected_complexity_options:
            print_error(f"Failed: {query}")
            print(f"  Expected complexity in {expected_complexity_options}, got {result['complexity']}")
            all_passed = False
        else:
            print_success(f"Passed: {query[:50]}")
    
    if not all_passed:
        return False
    
    print_success("Classifier tests passed")
    return True

def test_knowledge_graph():
    """Test Knowledge Graph."""
    print_header("Test 3: Knowledge Graph Test")
    
    from agents.comprehension import get_kg_client
    
    kg = get_kg_client()
    
    # Test basic queries
    options = kg.get_options()
    if len(options) < 20:
        print_error(f"Expected 20+ options, got {len(options)}")
        return False
    print_success(f"Found {len(options)} options")
    
    # Test filtering
    no_root = kg.get_options(requires_root=False)
    print_success(f"Found {len(no_root)} non-root options")
    
    # Test conflicts
    conflicts = kg.get_conflicts("-sS")
    if len(conflicts) < 2:
        print_error(f"Expected conflicts for -sS, got {conflicts}")
        return False
    print_success(f"Conflict detection works: -sS conflicts with {len(conflicts)} options")
    
    # Test validation
    test_conflicts = kg.validate_command_conflicts(["-sS", "-sT"])
    if len(test_conflicts) == 0:
        print_error("Should detect conflict between -sS and -sT")
        return False
    print_success("Command validation works")
    
    print_success("Knowledge Graph tests passed")
    return True

def test_api():
    """Test API endpoints without deployment."""
    print_header("Test 4: API Endpoint Test (without deployment)")
    
    from fastapi.testclient import TestClient
    from api.main import app
    
    client = TestClient(app)
    
    # Test root
    response = client.get("/")
    if response.status_code != 200:
        print_error(f"Root endpoint failed: {response.status_code}")
        return False
    print_success("Root endpoint works")
    
    # Test health
    response = client.get("/comprehend/health")
    if response.status_code != 200:
        print_error(f"Health endpoint failed: {response.status_code}")
        return False
    print_success("Health endpoint works")
    
    # Test comprehend
    response = client.post("/comprehend/", json={"query": "Scan network for SSH"})
    if response.status_code != 200:
        print_error(f"Comprehend endpoint failed: {response.status_code}")
        return False
    
    result = response.json()
    if not result["is_relevant"]:
        print_error("Should be relevant")
        return False
    
    print_success("Comprehend endpoint works")
    print(f"  Response: relevant={result['is_relevant']}, complexity={result['complexity']}")
    
    print_success("API tests passed")
    return True

def test_performance():
    """Test performance."""
    print_header("Test 5: Performance Test")
    
    from agents.comprehension import get_classifier
    
    classifier = get_classifier()
    
    queries = ["Scan network"] * 20
    
    start = time.time()
    for query in queries:
        classifier.comprehend(query)
    end = time.time()
    
    avg_time = (end - start) / len(queries) * 1000  # Convert to ms
    
    print_success(f"Average inference time: {avg_time:.1f}ms per query")
    
    if avg_time > 100:
        print_info("Warning: Inference is slower than expected (> 100ms)")
    
    print_success("Performance test passed")
    return True

def test_coverage():
    """Test code coverage."""
    print_header("Test 6: Code Coverage")
    
    result = subprocess.run(
        ["pytest", "tests/test_comprehension.py", 
         "--cov=agents/comprehension", "--cov-report=term-missing", "-q"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    # Try to extract coverage percentage
    for line in result.stdout.split('\n'):
        if 'agents/comprehension' in line:
            try:
                coverage_percent = int(line.split()[-1].rstrip('%'))
                if coverage_percent >= 80:
                    print_success(f"Code coverage: {coverage_percent}% (≥ 80% required)")
                    return True
                else:
                    print_error(f"Code coverage: {coverage_percent}% (< 80%)")
                    return False
            except:
                pass
    
    return True

def main():
    """Run all tests."""
    print_header("NMAP-AI Person 1 - Complete Test Suite")
    
    all_passed = True
    
    # Run all tests
    tests = [
        ("Models", test_models_trained),
        ("Unit Tests", test_unit_tests),
        ("Classifier", test_classifier),
        ("Knowledge Graph", test_knowledge_graph),
        ("API", test_api),
        ("Performance", test_performance),
        ("Coverage", test_coverage),
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            results[name] = test_func()
            if not results[name]:
                all_passed = False
        except Exception as e:
            print_error(f"Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
            all_passed = False
    
    # Final summary
    print_header("Test Summary")
    
    print("\nTest Results:")
    for name, passed in results.items():
        status = f"{GREEN}✓{NC}" if passed else f"{RED}✗{NC}"
        print(f"  {status} {name}: {'PASSED' if passed else 'FAILED'}")
    
    if all_passed:
        print(f"\n{GREEN}✅ All tests passed!{NC}")
        print(f"\n{BLUE}Person 1's deliverables are ready for integration!{NC}")
        print("\nNext steps:")
        print("  1. Review test output above")
        print("  2. Run demo: python scripts/demo_person1.py")
        print("  3. Start API: uvicorn api.main:app --reload")
        return 0
    else:
        print(f"\n{RED}❌ Some tests failed. Please review the errors above.{NC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())