#!/usr/bin/env python3
"""
Quick Integration Test Script
Run this to verify your setup is working

Usage:
    python verify_setup.py
"""

import os
import sys


def check_file(path, description):
    """Check if file exists"""
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"✅ {description}: {path} ({size:,} bytes)")
        return True
    else:
        print(f"❌ {description}: {path} (NOT FOUND)")
        return False


def main():
    print("=" * 70)
    print("🔍 NMAP-AI HARD GENERATOR - SETUP VERIFICATION")
    print("=" * 70)
    print()

    all_good = True

    # Check project structure
    print("📂 Checking project structure...")
    print()

    required_files = [
        ("agents/hard/t5_generator.py", "Main generator module"),
        ("agents/hard/adapter/adapter_config.json", "Adapter config"),
        ("agents/hard/adapter/adapter_model.safetensors", "Adapter weights"),
        ("agents/hard/adapter/spiece.model", "Tokenizer"),
        ("api/main.py", "FastAPI main app"),
        ("api/routers/nmap_ai.py", "API router"),
        ("requirements.txt", "Dependencies"),
    ]

    for path, desc in required_files:
        if not check_file(path, desc):
            all_good = False

    print()

    # Check Python imports
    print("🐍 Checking Python imports...")
    print()

    imports_to_check = [
        ("torch", "PyTorch"),
        ("transformers", "Transformers"),
        ("peft", "PEFT (LoRA)"),
        ("fastapi", "FastAPI"),
    ]

    for module, name in imports_to_check:
        try:
            __import__(module)
            print(f"✅ {name} installed")
        except ImportError:
            print(f"❌ {name} NOT installed")
            all_good = False

    print()

    # Try loading the generator
    print("🤖 Testing generator...")
    print()

    try:
        sys.path.insert(0, os.getcwd())
        from agents.hard.t5_generator import HardGenerator

        print("✅ Generator module imports successfully")

        # Try initializing
        gen = HardGenerator(adapter_path="./agents/hard/adapter")
        print("✅ Generator initializes successfully")

        # Try loading adapter
        print("   Loading adapter (this may take a few seconds)...")
        gen.load_adapter()
        print("✅ Adapter loads successfully")

        # Try generating
        print("   Generating test command...")
        cmd = gen.generate("UDP scan on port 161")
        print(f"✅ Generation works: {cmd}")

    except Exception as e:
        print(f"❌ Generator test failed: {e}")
        all_good = False

    print()
    print("=" * 70)

    if all_good:
        print("🎉 SUCCESS! Everything is set up correctly!")
        print()
        print("Next steps:")
        print("  1. Start FastAPI: uvicorn api.main:app --reload")
        print("  2. Open browser: http://localhost:8000/docs")
        print("  3. Test the /generate/hard endpoint")
    else:
        print("⚠️  ISSUES FOUND - Please fix the errors above")
        print()
        print("Common fixes:")
        print("  - Run: pip install -r requirements.txt")
        print("  - Make sure you're in the project root directory")
        print("  - Check that adapter files are in agents/hard/adapter/")

    print("=" * 70)

    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())