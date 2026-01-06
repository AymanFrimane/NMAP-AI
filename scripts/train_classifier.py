#!/usr/bin/env python3
"""
Training script for the Comprehension Agent
Trains the TF-IDF vectorizer and complexity classifier.
"""

import sys
from pathlib import Path
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.comprehension.classifier import NmapQueryClassifier


def main():
    parser = argparse.ArgumentParser(
        description="Train the Nmap query comprehension classifier"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="nmap_dataset.json",
        help="Path to the nmap dataset JSON file"
    )
    parser.add_argument(
        "--artifacts-dir",
        type=str,
        default="artifacts",
        help="Directory to save trained models"
    )
    
    args = parser.parse_args()
    
    # Resolve dataset path
    dataset_path = Path(args.dataset)
    if not dataset_path.is_absolute():
        dataset_path = project_root / dataset_path
    
    if not dataset_path.exists():
        print(f"Error: Dataset not found at {dataset_path}")
        sys.exit(1)
    
    print("="*60)
    print("NMAP-AI Comprehension Agent Training")
    print("="*60)
    print(f"Dataset: {dataset_path}")
    print(f"Artifacts: {args.artifacts_dir}")
    print()
    
    # Create classifier
    classifier = NmapQueryClassifier(artifacts_dir=args.artifacts_dir)
    
    # Train
    print("Training classifier...")
    accuracy, report = classifier.build_vocab_and_train(str(dataset_path))
    
    print("\n" + "="*60)
    print("Training Complete!")
    print("="*60)
    print(f"Accuracy: {accuracy:.1%}")
    print(f"Vocabulary size: {report['vocabulary_size']}")
    print(f"Train distribution: {report['train_distribution']}")
    print(f"Test distribution: {report['test_distribution']}")
    print()
    print("Models saved to:", args.artifacts_dir)
    print("  - tfidf.pkl")
    print("  - complexity_model.pkl")
    print()
    
    # Test the classifier
    print("Testing classifier...")
    test_queries = [
        ("Scan 192.168.1.0/24", True),
        ("Ping scan network", True),
        ("TCP SYN scan with version detection", True),
        ("Full port scan with OS detection and scripts", True),
        ("What is love?", False),
        ("Tell me a joke", False),
    ]
    
    print("\nTest Results:")
    print("-" * 60)
    for query, expected_relevant in test_queries:
        result = classifier.comprehend(query)
        status = "✓" if result["is_relevant"] == expected_relevant else "✗"
        print(f"{status} Query: {query[:40]:<40}")
        print(f"  Relevant: {result['is_relevant']}, Complexity: {result['complexity']}")
    
    print("\n" + "="*60)
    print("Training script completed successfully!")
    print("="*60)


if __name__ == "__main__":
    main()