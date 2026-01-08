"""
Dataset Analysis Script - Person 4
Analyzes nmap_dataset_final.json for patterns, flags, and complexity

Run with: python scripts/analyze_dataset.py
"""

import json
from collections import Counter
from pathlib import Path
import re

# ============================================================================
# CONFIGURATION
# ============================================================================

DATASET_PATH = "data/raw/nmap_dataset_final.json"
OUTPUT_PATH = "data/test/validator_test_cases.json"

# ============================================================================
# LOAD DATASET
# ============================================================================

def load_dataset(path: str):
    """Load dataset from JSON file"""
    print(f"Loading dataset from {path}...")
    with open(path, 'r') as f:
        data = json.load(f)
    print(f"✅ Loaded {len(data):,} examples")
    return data

# ============================================================================
# ANALYSIS FUNCTIONS
# ============================================================================

def extract_flags(command: str):
    """Extract all flags from command"""
    return re.findall(r'-[a-zA-Z0-9]+|--[\w-]+', command)

def analyze_flags(dataset):
    """Analyze flag frequency"""
    print("\n" + "="*70)
    print("FLAG FREQUENCY ANALYSIS")
    print("="*70)
    
    all_flags = []
    for item in dataset:
        flags = extract_flags(item['output'])
        all_flags.extend(flags)
    
    flag_counts = Counter(all_flags)
    
    print(f"\nTop 30 most common flags:")
    print(f"{'Flag':<15} {'Count':<10} {'Percentage':<12}")
    print("-" * 40)
    
    total = len(dataset)
    for flag, count in flag_counts.most_common(30):
        percentage = (count / total) * 100
        print(f"{flag:<15} {count:<10} {percentage:>6.1f}%")
    
    return flag_counts

def analyze_scan_types(dataset):
    """Analyze scan type distribution"""
    print("\n" + "="*70)
    print("SCAN TYPE DISTRIBUTION")
    print("="*70)
    
    scan_types = {
        '-sS': 'SYN Scan',
        '-sT': 'TCP Connect Scan',
        '-sU': 'UDP Scan',
        '-sN': 'Null Scan',
        '-sF': 'FIN Scan',
        '-sX': 'Xmas Scan',
        '-sA': 'ACK Scan',
        '-sW': 'Window Scan',
        '-sM': 'Maimon Scan',
        '-sn': 'Ping Scan (no port)',
    }
    
    counts = {flag: 0 for flag in scan_types.keys()}
    
    for item in dataset:
        flags = extract_flags(item['output'])
        for flag in scan_types.keys():
            if flag in flags:
                counts[flag] += 1
    
    print(f"\n{'Flag':<8} {'Name':<30} {'Count':<10} {'%':<8}")
    print("-" * 60)
    
    total = len(dataset)
    for flag, name in scan_types.items():
        count = counts[flag]
        percentage = (count / total) * 100
        print(f"{flag:<8} {name:<30} {count:<10} {percentage:>6.1f}%")
    
    return counts

def detect_conflicts(dataset):
    """Detect potential conflicts in dataset"""
    print("\n" + "="*70)
    print("CONFLICT DETECTION")
    print("="*70)
    
    scan_type_flags = ['-sS', '-sT', '-sU', '-sN', '-sF', '-sX', '-sA', '-sW', '-sM']
    
    conflicts = []
    for item in dataset:
        flags = extract_flags(item['output'])
        scan_flags = [f for f in flags if f in scan_type_flags]
        
        if len(scan_flags) > 1:
            conflicts.append({
                'command': item['output'],
                'conflicting_flags': scan_flags
            })
    
    print(f"\nFound {len(conflicts)} commands with potential conflicts")
    
    if conflicts:
        print("\nFirst 5 examples:")
        for i, conflict in enumerate(conflicts[:5], 1):
            print(f"\n{i}. {conflict['command']}")
            print(f"   Conflicts: {', '.join(conflict['conflicting_flags'])}")
    else:
        print("✅ No conflicts detected in dataset!")
    
    return conflicts

def estimate_complexity(command: str):
    """Estimate command complexity"""
    flags = extract_flags(command)
    
    # Simple heuristics
    if len(flags) <= 2:
        return "EASY"
    elif len(flags) <= 5:
        return "MEDIUM"
    else:
        return "HARD"

def analyze_complexity(dataset):
    """Analyze complexity distribution"""
    print("\n" + "="*70)
    print("COMPLEXITY DISTRIBUTION")
    print("="*70)
    
    complexity_counts = Counter()
    
    for item in dataset:
        complexity = estimate_complexity(item['output'])
        complexity_counts[complexity] += 1
    
    total = len(dataset)
    print(f"\n{'Complexity':<15} {'Count':<10} {'Percentage':<12}")
    print("-" * 40)
    
    for complexity in ['EASY', 'MEDIUM', 'HARD']:
        count = complexity_counts[complexity]
        percentage = (count / total) * 100
        print(f"{complexity:<15} {count:<10} {percentage:>6.1f}%")
    
    return complexity_counts

def analyze_targets(dataset):
    """Analyze target types"""
    print("\n" + "="*70)
    print("TARGET TYPE ANALYSIS")
    print("="*70)
    
    ip_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?!/)'
    cidr_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d+'
    ipv6_pattern = r'[0-9a-fA-F:]+::[0-9a-fA-F:]+'
    
    target_types = {
        'Single IP': 0,
        'CIDR Range': 0,
        'IPv6': 0,
        'Domain': 0,
        'Multiple': 0
    }
    
    for item in dataset:
        cmd = item['output']
        
        if re.search(cidr_pattern, cmd):
            target_types['CIDR Range'] += 1
        elif re.search(ipv6_pattern, cmd):
            target_types['IPv6'] += 1
        elif re.search(ip_pattern, cmd):
            # Check if multiple IPs
            if len(re.findall(ip_pattern, cmd)) > 1:
                target_types['Multiple'] += 1
            else:
                target_types['Single IP'] += 1
        else:
            target_types['Domain'] += 1
    
    total = len(dataset)
    print(f"\n{'Type':<20} {'Count':<10} {'Percentage':<12}")
    print("-" * 45)
    
    for target_type, count in target_types.items():
        percentage = (count / total) * 100
        print(f"{target_type:<20} {count:<10} {percentage:>6.1f}%")
    
    return target_types

def generate_test_cases(dataset, num_cases=100):
    """Generate test cases for validator"""
    print("\n" + "="*70)
    print("GENERATING TEST CASES")
    print("="*70)
    
    # Sample diverse commands
    test_cases = []
    
    # Easy commands
    easy = [item for item in dataset if estimate_complexity(item['output']) == 'EASY']
    test_cases.extend(easy[:num_cases//3])
    
    # Medium commands
    medium = [item for item in dataset if estimate_complexity(item['output']) == 'MEDIUM']
    test_cases.extend(medium[:num_cases//3])
    
    # Hard commands
    hard = [item for item in dataset if estimate_complexity(item['output']) == 'HARD']
    test_cases.extend(hard[:num_cases//3])
    
    print(f"✅ Generated {len(test_cases)} test cases")
    print(f"   - EASY: {len([c for c in test_cases if estimate_complexity(c['output']) == 'EASY'])}")
    print(f"   - MEDIUM: {len([c for c in test_cases if estimate_complexity(c['output']) == 'MEDIUM'])}")
    print(f"   - HARD: {len([c for c in test_cases if estimate_complexity(c['output']) == 'HARD'])}")
    
    return test_cases

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*70)
    print("NMAP DATASET ANALYSIS - PERSON 4")
    print("="*70)
    
    # Load dataset
    dataset = load_dataset(DATASET_PATH)
    
    # Run analyses
    flag_counts = analyze_flags(dataset)
    scan_counts = analyze_scan_types(dataset)
    conflicts = detect_conflicts(dataset)
    complexity_counts = analyze_complexity(dataset)
    target_types = analyze_targets(dataset)
    
    # Generate test cases
    test_cases = generate_test_cases(dataset)
    
    # Save test cases
    output_dir = Path(OUTPUT_PATH).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(test_cases, f, indent=2)
    
    print(f"\n✅ Test cases saved to: {OUTPUT_PATH}")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total examples: {len(dataset):,}")
    print(f"Unique flags: {len(flag_counts)}")
    print(f"Conflicts found: {len(conflicts)}")
    print(f"Test cases generated: {len(test_cases)}")
    print("\nTop 5 flags:")
    for flag, count in flag_counts.most_common(5):
        print(f"  {flag}: {count:,} times")
    
    print("\n" + "="*70)
    print("✅ Analysis complete!")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()