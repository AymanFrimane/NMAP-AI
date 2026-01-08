#!/usr/bin/env python3
"""
Simple test script for Hard Generator API
Run this while your FastAPI server is running
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("\n" + "=" * 70)
    print("🏥 Testing Health Endpoint")
    print("=" * 70)

    try:
        response = requests.get(f"{BASE_URL}/nmap/hard/health", timeout=5)
        data = response.json()

        print(f"Status Code: {response.status_code}")
        print(f"Model Loaded: {data.get('hard_generator_loaded', False)}")
        print(f"Status: {data.get('status', 'unknown')}")

        if data.get('error'):
            print(f"❌ Error: {data['error']}")

        if data.get('message'):
            print(f"💡 {data['message']}")

        return data.get('hard_generator_loaded', False)

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_generation(query, timeout=180):
    """Test command generation"""
    print("\n" + "=" * 70)
    print("🚀 Testing Command Generation")
    print("=" * 70)
    print(f"Query: {query}")
    print(f"Timeout: {timeout}s")
    print("\n⏳ Sending request...")
    print("   (This takes 30-90s on CPU - watch server logs for progress)\n")

    # Progress indicator
    def show_progress():
        for i in range(timeout):
            print(".", end="", flush=True)
            time.sleep(1)
            if i % 10 == 9:
                print(f" {i + 1}s", end="", flush=True)

    start_time = time.time()

    try:
        import threading

        # Start progress indicator in background
        progress_thread = threading.Thread(target=show_progress, daemon=True)
        progress_thread.start()

        # Make request
        response = requests.post(
            f"{BASE_URL}/nmap/generate/hard",
            json={"query": query},
            timeout=timeout
        )

        elapsed = time.time() - start_time

        print(f"\n\n✅ Response received in {elapsed:.1f}s")
        print(f"Status Code: {response.status_code}\n")

        if response.status_code == 200:
            result = response.json()
            print("-" * 70)
            print(f"Query:      {result['query']}")
            print(f"Command:    {result['command']}")
            print(f"Complexity: {result['complexity']}")
            print(f"Confidence: {result['confidence']}")
            print("-" * 70)
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"\n\n⏰ Request timed out after {elapsed:.1f}s")
        print("💡 Model is still generating. Check server logs or increase timeout.")
        return False

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n\n❌ Error after {elapsed:.1f}s: {e}")
        return False


def main():
    """Run tests"""
    print("\n" + "=" * 70)
    print("🧪 NMAP-AI Hard Generator API Test")
    print("=" * 70)
    print("\n⚠️  Make sure your FastAPI server is running:")
    print("   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000\n")

    input("Press ENTER to start tests (or Ctrl+C to cancel)...")

    # Test 1: Health check
    is_loaded = test_health()

    if not is_loaded:
        print("\n⚠️  Model not loaded yet. First generation will trigger loading.")

    input("\nPress ENTER to test generation...")

    # Test 2: Simple generation
    print("\n" + "=" * 70)
    print("📝 Test 1: Simple Query")
    print("=" * 70)
    success = test_generation("UDP scan on port 161", timeout=120)

    if not success:
        print("\n❌ First test failed. Check server logs for errors.")
        sys.exit(1)

    input("\nPress ENTER for next test...")

    # Test 3: Your original query
    print("\n" + "=" * 70)
    print("📝 Test 2: Complex Query")
    print("=" * 70)
    success = test_generation(
        "Scan all TCP ports with SYN scan and detect service versions on 192.168.1.10",
        timeout=180
    )

    if not success:
        print("\n❌ Second test failed.")
        sys.exit(1)

    # Test 4: Final health check
    test_health()

    print("\n" + "=" * 70)
    print("✅ All Tests Passed!")
    print("=" * 70)
    print("\n📊 Performance Notes:")
    print("   - Model loading: 30-60s (first time only)")
    print("   - Generation on CPU: 20-90s per query")
    print("   - GPU would be 10-50x faster")
    print("\n💡 Server logs show detailed progress for each step")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)