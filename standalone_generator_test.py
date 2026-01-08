#!/usr/bin/env python3
"""
Test the Hard Generator directly WITHOUT FastAPI
This will help diagnose if the issue is with the generator or the API
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_generator_directly():
    """Test generator without API overhead"""

    print("=" * 70)
    print("🧪 Testing Hard Generator Directly (No FastAPI)")
    print("=" * 70)
    print()

    print("📦 Step 1: Importing generator...")
    try:
        from agents.hard.t5_generator import HardGenerator
        print("✅ Import successful\n")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("🔧 Step 2: Creating generator instance...")
    try:
        generator = HardGenerator(adapter_path="./agents/hard/adapter")
        print("✅ Instance created\n")
    except Exception as e:
        print(f"❌ Creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("📥 Step 3: Loading adapter (this takes 30-60s)...")
    print("    Watch for detailed progress...\n")
    try:
        generator.load_adapter()
        print("\n✅ Adapter loaded successfully\n")
    except Exception as e:
        print(f"\n❌ Loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("🚀 Step 4: Testing generation...")
    test_queries = [
        "UDP scan on port 161",
        "UDP SNMP brute force on 10.0.0.1",
        "Scan all TCP ports with SYN scan and detect service versions on 192.168.1.10"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n[Test {i}] Query: {query}")
        print("    Generating (20-60s on CPU)...")

        try:
            command = generator.generate(query)
            print(f"    ✅ Result: {command}\n")
        except Exception as e:
            print(f"    ❌ Generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    print("=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print()
    print("💡 Generator works fine. If API still fails, the issue is with FastAPI integration.")
    return True


def test_imports():
    """Test that all required packages are available"""

    print("=" * 70)
    print("📦 Testing Package Imports")
    print("=" * 70)
    print()

    packages = [
        ("torch", "PyTorch"),
        ("transformers", "Transformers"),
        ("peft", "PEFT (LoRA)"),
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
    ]

    all_ok = True
    for module_name, display_name in packages:
        try:
            __import__(module_name)
            print(f"✅ {display_name}")
        except ImportError as e:
            print(f"❌ {display_name}: {e}")
            all_ok = False

    print()
    return all_ok


def check_adapter_files():
    """Check that adapter files exist"""

    print("=" * 70)
    print("📁 Checking Adapter Files")
    print("=" * 70)
    print()

    adapter_path = "./agents/hard/adapter"
    required_files = [
        "adapter_config.json",
        "adapter_model.safetensors",
        "spiece.model"
    ]

    all_ok = True
    for filename in required_files:
        filepath = os.path.join(adapter_path, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"✅ {filename} ({size:,} bytes)")
        else:
            print(f"❌ {filename} NOT FOUND")
            all_ok = False

    print()
    return all_ok


def main():
    """Run all diagnostic tests"""

    print("\n" + "=" * 70)
    print("🔍 HARD GENERATOR DIAGNOSTIC TEST")
    print("=" * 70)
    print()

    # Test 1: Imports
    if not test_imports():
        print("\n❌ Some packages are missing. Run: pip install -r requirements.txt")
        return 1

    # Test 2: Files
    if not check_adapter_files():
        print("\n❌ Some adapter files are missing.")
        return 1

    input("Press ENTER to test generator (will take ~60s)...")

    # Test 3: Generator
    if not test_generator_directly():
        print("\n❌ Generator test failed. Check errors above.")
        return 1

    print("\n" + "=" * 70)
    print("✅ DIAGNOSIS COMPLETE - Generator works fine!")
    print("=" * 70)
    print()
    print("🔧 Next Steps:")
    print("   1. If API still fails, check for:")
    print("      - Timeout issues in FastAPI")
    print("      - Memory issues (check Task Manager)")
    print("      - Conflicting imports")
    print()
    print("   2. Try running API with:")
    print("      uvicorn api.main:app --reload --timeout-keep-alive 300")
    print()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)