"""
Manual API Testing Script (No Server Needed!)
Uses FastAPI TestClient to test endpoints without uvicorn

Run from project root: python manual_api_test.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("="*70)
print("NMAP-AI Manual API Testing (No Server Required!)")
print("="*70)
print()

# Check imports first
print("Step 1: Checking imports...")
print("-"*70)

try:
    from fastapi.testclient import TestClient
    print("✓ FastAPI TestClient available")
except ImportError as e:
    print(f"✗ FastAPI not installed: {e}")
    print("  Run: pip install fastapi httpx")
    sys.exit(1)

try:
    from api.main import app
    print("✓ API application loaded")
except ImportError as e:
    print(f"✗ Cannot import API: {e}")
    print("  Make sure api/main.py and api/__init__.py exist")
    sys.exit(1)

try:
    from agents.comprehension import get_classifier
    print("✓ Comprehension agent available")
except ImportError as e:
    print(f"✗ Cannot import agent: {e}")
    print("  Make sure agents/comprehension/__init__.py exists")
    sys.exit(1)

print()

# Create test client
print("Step 2: Creating test client...")
print("-"*70)
client = TestClient(app)
print("✓ Test client created (no server needed!)")
print()

# Test queries
test_queries = [
    {
        "name": "Simple Scan",
        "query": "Scan 192.168.1.0/24",
        "expected_relevant": True,
        "expected_complexity": "EASY"
    },
    {
        "name": "TCP SYN Scan",
        "query": "TCP SYN scan with version detection",
        "expected_relevant": True,
        "expected_complexity": "MEDIUM"
    },
    {
        "name": "Complex Scan",
        "query": "Full port scan with OS detection, version detection, and vulnerability scripts",
        "expected_relevant": True,
        "expected_complexity": ["MEDIUM", "HARD"]  # Accept either
    },
    {
        "name": "Port Scan",
        "query": "Scan ports 80 and 443",
        "expected_relevant": True,
        "expected_complexity": "EASY"
    },
    {
        "name": "Irrelevant Query",
        "query": "What is love?",
        "expected_relevant": False,
        "expected_complexity": None
    }
]

# Run tests
print("Step 3: Testing API endpoints...")
print("="*70)
print()

results = {
    "passed": 0,
    "failed": 0,
    "errors": 0
}

# Test 1: Root endpoint
print("Test 1: Root Endpoint")
print("-"*70)
try:
    response = client.get("/")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Status: {response.status_code}")
        print(f"  API Name: {data.get('name')}")
        print(f"  Version: {data.get('version')}")
        results["passed"] += 1
    else:
        print(f"✗ Status: {response.status_code} (expected 200)")
        results["failed"] += 1
except Exception as e:
    print(f"✗ Error: {e}")
    results["errors"] += 1
print()

# Test 2: Health endpoint
print("Test 2: Health Check")
print("-"*70)
try:
    response = client.get("/comprehend/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Status: {response.status_code}")
        print(f"  Health: {data.get('status')}")
        print(f"  Models: {data.get('models_loaded')}")
        results["passed"] += 1
    else:
        print(f"✗ Status: {response.status_code} (expected 200)")
        results["failed"] += 1
except Exception as e:
    print(f"✗ Error: {e}")
    results["errors"] += 1
print()

# Test 3-7: Comprehend endpoint with various queries
for i, test in enumerate(test_queries, start=3):
    print(f"Test {i}: {test['name']}")
    print("-"*70)
    
    try:
        response = client.post(
            "/comprehend/",
            json={"query": test["query"]}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check response structure
            has_intent = "intent" in data
            has_relevant = "is_relevant" in data
            has_complexity = "complexity" in data
            
            if not all([has_intent, has_relevant, has_complexity]):
                print(f"✗ Missing fields in response")
                print(f"  Has intent: {has_intent}")
                print(f"  Has is_relevant: {has_relevant}")
                print(f"  Has complexity: {has_complexity}")
                results["failed"] += 1
                print()
                continue
            
            # Verify relevance
            relevance_correct = data["is_relevant"] == test["expected_relevant"]
            
            # Verify complexity (handle list of expected values)
            if isinstance(test["expected_complexity"], list):
                complexity_correct = data["complexity"] in test["expected_complexity"]
            else:
                complexity_correct = data["complexity"] == test["expected_complexity"]
            
            if relevance_correct and complexity_correct:
                print(f"✓ Query: {test['query']}")
                print(f"  Intent: {data['intent']}")
                print(f"  Relevant: {data['is_relevant']}")
                print(f"  Complexity: {data['complexity']}")
                results["passed"] += 1
            else:
                print(f"✗ Query: {test['query']}")
                print(f"  Expected relevant: {test['expected_relevant']}, Got: {data['is_relevant']}")
                print(f"  Expected complexity: {test['expected_complexity']}, Got: {data['complexity']}")
                results["failed"] += 1
        else:
            print(f"✗ Status: {response.status_code} (expected 200)")
            print(f"  Response: {response.text}")
            results["failed"] += 1
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        results["errors"] += 1
    
    print()

# Summary
print("="*70)
print("Test Summary")
print("="*70)
print(f"Passed:  {results['passed']}")
print(f"Failed:  {results['failed']}")
print(f"Errors:  {results['errors']}")
print(f"Total:   {results['passed'] + results['failed'] + results['errors']}")
print()

if results["failed"] == 0 and results["errors"] == 0:
    print("✅ All tests passed!")
    print()
    print("Next steps:")
    print("  1. Start server: uvicorn api.main:app --reload")
    print("  2. Open docs: http://localhost:8000/docs")
    print("  3. Test in browser")
    sys.exit(0)
else:
    print("❌ Some tests failed!")
    print()
    print("Troubleshooting:")
    if results["errors"] > 0:
        print("  - Check that models are trained (run train_classifier.py)")
        print("  - Check that all __init__.py files exist")
        print("  - Check that api/main.py is not empty")
    if results["failed"] > 0:
        print("  - Check classifier training data")
        print("  - Review test expectations")
    sys.exit(1)