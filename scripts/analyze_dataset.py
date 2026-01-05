#!/usr/bin/env python3
"""
Dataset Analysis Script - Person 4
Analyzes nmap_dataset_final.json for patterns
"""

import json
from collections import Counter
import re

DATASET_PATH = "data/raw/nmap_dataset_final.json"

def load_dataset():
    print("Loading dataset...")
    with open(DATASET_PATH, 'r') as f:
        data = json.load(f)
    print(f"✅ Loaded {len(data):,} examples")
    return data

def extract_flags(command):
    return re.findall(r'-[a-zA-Z0-9]+|--[\w-]+', command)

def analyze_flags(dataset):
    print("\n" + "="*70)
    print("FLAG FREQUENCY ANALYSIS")
    print("="*70)
    
    all_flags = []
    for item in dataset:
        flags = extract_flags(item['output'])
        all_flags.extend(flags)
    
    flag_counts = Counter(all_flags)
    
    print(f"\nTop 20 most common flags:")
    print(f"{'Flag':<15} {'Count':<10} {'%':<10}")
    print("-" * 40)
    
    total = len(dataset)
    for flag, count in flag_counts.most_common(20):
        percentage = (count / total) * 100
        print(f"{flag:<15} {count:<10,} {percentage:>6.1f}%")
    
    return flag_counts

def main():
    print("\n" + "="*70)
    print("NMAP DATASET ANALYSIS - PERSON 4")
    print("="*70)
    
    dataset = load_dataset()
    flag_counts = analyze_flags(dataset)
    
    print(f"\n✅ Analysis complete!")
    print(f"Total unique flags: {len(flag_counts)}")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
