#!/usr/bin/env python3
"""
Standalone Hard Model Generator
Works exactly like standalone_generator_test.py but accepts query as input
Can be called from command line or as subprocess from FastAPI

Usage:
    python hard_model_standalone.py "UDP scan on port 161"
    
Or with stdin:
    echo "UDP scan on port 161" | python hard_model_standalone.py
"""

import sys
import os
import json

# Add project root to path (same as test script)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Change to project root directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def generate_command(query: str) -> str:
    """
    Generate hard nmap command - exact same logic as test script
    """
    print("=" * 70, file=sys.stderr)
    print("🧪 Generating Hard Command (Standalone)", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print()

    # Step 1: Import generator (same as test script)
    print("📦 Step 1: Importing generator...", file=sys.stderr)
    try:
        from agents.hard.t5_generator import HardGenerator
        print("✅ Import successful\n", file=sys.stderr)
    except Exception as e:
        print(f"❌ Import failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Step 2: Create generator instance (same as test script)
    print("🔧 Step 2: Creating generator instance...", file=sys.stderr)
    try:
        generator = HardGenerator(adapter_path="./agents/hard/adapter")
        print("✅ Instance created\n", file=sys.stderr)
    except Exception as e:
        print(f"❌ Creation failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Step 3: Load adapter (same as test script)
    print("📥 Step 3: Loading adapter (this takes 30-60s)...", file=sys.stderr)
    print("    Watch for detailed progress...\n", file=sys.stderr)
    try:
        generator.load_adapter()
        print("\n✅ Adapter loaded successfully\n", file=sys.stderr)
    except Exception as e:
        print(f"\n❌ Loading failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Step 4: Generate command (same as test script)
    print(f"🚀 Step 4: Generating command for: {query}", file=sys.stderr)
    print("    Generating (20-60s on CPU)...", file=sys.stderr)
    try:
        command = generator.generate(query)
        print(f"    ✅ Result: {command}\n", file=sys.stderr)
        return command
    except Exception as e:
        print(f"    ❌ Generation failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point"""
    # Get query from command line or stdin
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        # Read from stdin
        query = sys.stdin.read().strip()
    
    if not query:
        print("Error: No query provided", file=sys.stderr)
        print("Usage: python hard_model_standalone.py 'your query here'", file=sys.stderr)
        sys.exit(1)
    
    try:
        command = generate_command(query)
        
        # Output result as JSON for easy parsing
        result = {
            "query": query,
            "command": command,
            "complexity": "HARD",
            "confidence": 0.85
        }
        
        print(json.dumps(result))
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
