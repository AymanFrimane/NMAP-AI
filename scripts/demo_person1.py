#!/usr/bin/env python3
"""
Demo script for Person 1's Comprehension Agent
Shows classifier and Knowledge Graph in action.
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.comprehension import get_classifier, get_kg_client


def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def demo_classifier():
    """Demonstrate the classifier functionality."""
    print_header("CLASSIFIER DEMO")
    
    classifier = get_classifier()
    
    test_queries = [
        "Scan 192.168.1.0/24 for web servers",
        "Perform TCP SYN scan with OS detection",
        "Full port scan with vulnerability scripts and aggressive timing",
        "Ping scan the local network",
        "What is the capital of France?",
        "How to bake a chocolate cake?",
        "Find all HTTP and HTTPS servers on subnet",
        "UDP scan with version detection on port 161",
    ]
    
    print("\nAnalyzing queries...\n")
    
    for query in test_queries:
        result = classifier.comprehend(query)
        
        # Format output
        relevance = "✓ RELEVANT" if result["is_relevant"] else "✗ NOT RELEVANT"
        complexity = result["complexity"] if result["complexity"] else "N/A"
        
        print(f"Query: {query}")
        print(f"  → {relevance}")
        if result["is_relevant"]:
            print(f"  → Complexity: {complexity}")
        print()


def demo_knowledge_graph():
    """Demonstrate Knowledge Graph queries."""
    print_header("KNOWLEDGE GRAPH DEMO")
    
    kg = get_kg_client()
    
    # Demo 1: Get all scan types
    print("\n1. All Scan Types:")
    print("-" * 70)
    scan_types = kg.get_options(category="SCAN_TYPE")
    for opt in scan_types:
        root = "🔒 ROOT" if opt.requires_root else "👤 USER"
        print(f"  {root}  {opt.name:<10} - {opt.description}")
    
    # Demo 2: Get non-root options
    print("\n2. Options That DON'T Require Root:")
    print("-" * 70)
    no_root = kg.get_options(requires_root=False)[:5]  # Show first 5
    for opt in no_root:
        print(f"  {opt.name:<15} [{opt.category}] - {opt.description}")
    print(f"  ... and {len(kg.get_options(requires_root=False)) - 5} more")
    
    # Demo 3: Get conflicts
    print("\n3. Conflict Detection:")
    print("-" * 70)
    
    test_flags = ["-sS", "-sT", "-sU", "-sn"]
    for flag in test_flags:
        conflicts = kg.get_conflicts(flag)
        if conflicts:
            print(f"  {flag} conflicts with: {', '.join(conflicts)}")
    
    # Demo 4: Validate command
    print("\n4. Command Validation:")
    print("-" * 70)
    
    test_commands = [
        (["-sS", "-p", "80,443", "-sV"], "Valid command"),
        (["-sS", "-sT"], "Invalid: Conflicting scan types"),
        (["-p-", "-F"], "Invalid: Conflicting port specs"),
    ]
    
    for flags, description in test_commands:
        conflicts = kg.validate_command_conflicts(flags)
        status = "✓ VALID" if not conflicts else "✗ INVALID"
        print(f"  {status}  {' '.join(flags)}")
        print(f"         → {description}")
        if conflicts:
            for flag, conflicting in conflicts.items():
                print(f"         → {flag} conflicts with {', '.join(conflicting)}")
        print()


def demo_integration():
    """Demonstrate integrated workflow."""
    print_header("INTEGRATED WORKFLOW DEMO")
    
    classifier = get_classifier()
    kg = get_kg_client()
    
    query = "Scan network for SSH servers without requiring root privileges"
    
    print(f"\n🔍 Query: '{query}'")
    print("\nStep 1: Comprehension")
    print("-" * 70)
    
    result = classifier.comprehend(query)
    print(f"  Intent: {result['intent']}")
    print(f"  Relevant: {result['is_relevant']}")
    print(f"  Complexity: {result['complexity']}")
    
    if result["is_relevant"]:
        print("\nStep 2: Knowledge Graph Query")
        print("-" * 70)
        
        # Get appropriate scan options
        if result["complexity"] == "EASY":
            print("  → Querying simple scan options (no root required)")
            options = kg.get_options(requires_root=False, category="SCAN_TYPE")
        else:
            print("  → Querying advanced scan options")
            options = kg.get_options(category="SCAN_TYPE")
        
        print(f"  → Found {len(options)} scan type options")
        
        # Show a recommended command template
        print("\nStep 3: Command Template")
        print("-" * 70)
        print("  Suggested approach:")
        print("    nmap -sT -p 22 192.168.1.0/24")
        print("    └─┬─┘ └──┬──┘ └──────┬──────┘")
        print("      │      │           └─ Target network")
        print("      │      └─ SSH port (22)")
        print("      └─ TCP connect scan (no root needed)")


def main():
    """Run all demos."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║         NMAP-AI Comprehension Agent Demo                            ║
║         Person 1's Contribution                                      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Demo 1: Classifier
        demo_classifier()
        
        # Demo 2: Knowledge Graph
        demo_knowledge_graph()
        
        # Demo 3: Integration
        demo_integration()
        
        print_header("DEMO COMPLETED")
        print("""
All systems operational! ✓

Next steps:
  1. Train with full dataset: python scripts/train_classifier.py
  2. Start API server: uvicorn api.main:app --reload
  3. Visit http://localhost:8000/docs
        """)
        
    except RuntimeError as e:
        print(f"\n⚠ Error: {e}")
        print("\n📝 Note: If models aren't trained yet, run:")
        print("    python scripts/train_classifier.py")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()