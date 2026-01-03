"""
Conflict Checker - Person 4
Detects conflicting nmap flags using Knowledge Graph or hardcoded fallback

IMPROVED VERSION: Detects basic conflicts even without KG
"""

import re
from typing import Tuple, List, Optional

# ============================================================================
# HARDCODED CONFLICT RULES (FALLBACK WITHOUT KG)
# ============================================================================

# These are the most common conflicts that should ALWAYS be detected
HARDCODED_CONFLICTS = {
    # Scan type conflicts - can only use ONE of these at a time
    'scan_types': {
        '-sS': ['-sT', '-sA', '-sW', '-sM', '-sU', '-sN', '-sF', '-sX'],
        '-sT': ['-sS', '-sA', '-sW', '-sM', '-sU', '-sN', '-sF', '-sX'],
        '-sU': ['-sS', '-sT', '-sA', '-sW', '-sM', '-sN', '-sF', '-sX'],
        '-sN': ['-sS', '-sT', '-sA', '-sW', '-sM', '-sU', '-sF', '-sX'],
        '-sF': ['-sS', '-sT', '-sA', '-sW', '-sM', '-sU', '-sN', '-sX'],
        '-sX': ['-sS', '-sT', '-sA', '-sW', '-sM', '-sU', '-sN', '-sF'],
        '-sA': ['-sS', '-sT', '-sW', '-sM', '-sU', '-sN', '-sF', '-sX'],
        '-sW': ['-sS', '-sT', '-sA', '-sM', '-sU', '-sN', '-sF', '-sX'],
        '-sM': ['-sS', '-sT', '-sA', '-sW', '-sU', '-sN', '-sF', '-sX'],
    },
    
    # Special conflicts
    'special': {
        '-sn': ['-p'],  # Ping scan doesn't use ports
        '-Pn': ['-PS', '-PA', '-PU', '-PE', '-PP', '-PM'],  # No ping means no ping types
    }
}

# Flags that require root/sudo privileges
ROOT_REQUIRED_FLAGS = [
    '-sS',  # SYN scan
    '-sU',  # UDP scan
    '-sN',  # Null scan
    '-sF',  # FIN scan
    '-sX',  # Xmas scan
    '-sA',  # ACK scan
    '-sW',  # Window scan
    '-sM',  # Maimon scan
    '-O',   # OS detection
    '--traceroute',  # Traceroute
]


# ============================================================================
# FLAG EXTRACTION
# ============================================================================

def extract_flags(command: str) -> List[str]:
    """
    Extract nmap flags from command
    
    Args:
        command: Nmap command string
        
    Returns:
        List of flags found in command
        
    Examples:
        >>> extract_flags("nmap -sS -sV -p 80,443 192.168.1.1")
        ['-sS', '-sV', '-p']
    """
    # Match flags like -sS, -p, --script, -T4, etc.
    flags = re.findall(r'-[a-zA-Z0-9]+|--[\w-]+', command)
    return flags


# ============================================================================
# CONFLICT DETECTION (IMPROVED)
# ============================================================================

def validate_conflicts(command: str, kg_client=None) -> Tuple[bool, str]:
    """
    Validate that command has no conflicting flags
    
    IMPROVED: Detects basic conflicts even without Knowledge Graph
    
    Args:
        command: Nmap command to validate
        kg_client: Knowledge Graph client (optional)
        
    Returns:
        (is_valid, message) tuple
        
    Examples:
        >>> validate_conflicts("nmap -sS -sT 192.168.1.1")
        (False, "Conflict detected: -sS conflicts with -sT")
        
        >>> validate_conflicts("nmap -sn -p 80 192.168.1.1")
        (False, "Conflict detected: -sn conflicts with -p")
    """
    flags = extract_flags(command)
    
    # Try to use Knowledge Graph if available
    if kg_client is not None:
        try:
            # Use KG to check conflicts
            for flag in flags:
                conflicts = kg_client.get_conflicts(flag)
                if conflicts:
                    for conflict_flag in conflicts:
                        if conflict_flag in flags:
                            return (False, f"Conflict detected: {flag} conflicts with {conflict_flag}")
            return (True, "No conflicts detected (verified with Knowledge Graph)")
        except Exception as e:
            # KG failed, fall back to hardcoded rules
            pass
    
    # FALLBACK: Use hardcoded conflict rules
    # Check scan type conflicts
    for flag in flags:
        if flag in HARDCODED_CONFLICTS['scan_types']:
            conflicting = HARDCODED_CONFLICTS['scan_types'][flag]
            for conflict_flag in conflicting:
                if conflict_flag in flags:
                    return (False, f"Conflict detected: {flag} conflicts with {conflict_flag} (cannot use multiple scan types)")
    
    # Check special conflicts
    for flag in flags:
        if flag in HARDCODED_CONFLICTS['special']:
            conflicting = HARDCODED_CONFLICTS['special'][flag]
            for conflict_flag in conflicting:
                if conflict_flag in flags:
                    return (False, f"Conflict detected: {flag} conflicts with {conflict_flag}")
    
    # No conflicts found
    return (True, "No conflicts detected (using fallback rules)")


# ============================================================================
# ROOT REQUIREMENT CHECK
# ============================================================================

def check_requires_root(command: str, kg_client=None) -> Tuple[bool, List[str]]:
    """
    Check if command requires root/sudo privileges
    
    Args:
        command: Nmap command to check
        kg_client: Knowledge Graph client (optional)
        
    Returns:
        (requires_root, list_of_flags_requiring_root)
        
    Examples:
        >>> check_requires_root("nmap -sS 192.168.1.1")
        (True, ['-sS'])
        
        >>> check_requires_root("nmap -sT 192.168.1.1")
        (False, [])
    """
    flags = extract_flags(command)
    
    # Try to use Knowledge Graph if available
    if kg_client is not None:
        try:
            options = kg_client.get_options(requires_root=True)
            root_flags_from_kg = [opt['flag'] for opt in options]
            
            root_flags_found = []
            for flag in flags:
                if flag in root_flags_from_kg:
                    root_flags_found.append(flag)
            
            return (len(root_flags_found) > 0, root_flags_found)
        except Exception:
            # KG failed, fall back to hardcoded list
            pass
    
    # FALLBACK: Use hardcoded list
    root_flags_found = []
    for flag in flags:
        if flag in ROOT_REQUIRED_FLAGS:
            root_flags_found.append(flag)
    
    return (len(root_flags_found) > 0, root_flags_found)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_all_conflicts(flag: str, kg_client=None) -> List[str]:
    """
    Get all flags that conflict with the given flag
    
    Args:
        flag: Flag to check
        kg_client: Knowledge Graph client (optional)
        
    Returns:
        List of conflicting flags
    """
    # Try KG first
    if kg_client is not None:
        try:
            return kg_client.get_conflicts(flag)
        except Exception:
            pass
    
    # Fallback to hardcoded
    all_conflicts = []
    
    # Check scan types
    if flag in HARDCODED_CONFLICTS['scan_types']:
        all_conflicts.extend(HARDCODED_CONFLICTS['scan_types'][flag])
    
    # Check special conflicts
    if flag in HARDCODED_CONFLICTS['special']:
        all_conflicts.extend(HARDCODED_CONFLICTS['special'][flag])
    
    return all_conflicts


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test cases
    test_cases = [
        ("nmap -sV 192.168.1.1", True, "No conflicts"),
        ("nmap -sS -sT 192.168.1.1", False, "SYN + TCP Connect conflict"),
        ("nmap -sn -p 80 192.168.1.1", False, "Ping scan + port spec conflict"),
        ("nmap -sS -sU 192.168.1.1", False, "SYN + UDP conflict"),
        ("nmap -Pn -PS 192.168.1.1", False, "No ping + ping type conflict"),
    ]
    
    print("Testing Conflict Checker (without KG):")
    print("=" * 60)
    
    for command, expected, description in test_cases:
        valid, msg = validate_conflicts(command, kg_client=None)
        status = "✅" if valid == expected else "❌"
        print(f"{status} {description}")
        print(f"   Command: {command}")
        print(f"   Expected: {expected}, Got: {valid}")
        print(f"   Message: {msg}")
        print()
    
    # Test root requirement
    print("\nTesting Root Requirement Check:")
    print("=" * 60)
    
    root_test_cases = [
        ("nmap -sS 192.168.1.1", True, "SYN scan requires root"),
        ("nmap -sT 192.168.1.1", False, "TCP Connect doesn't require root"),
        ("nmap -O 192.168.1.1", True, "OS detection requires root"),
    ]
    
    for command, expected, description in root_test_cases:
        requires_root, flags = check_requires_root(command, kg_client=None)
        status = "✅" if requires_root == expected else "❌"
        print(f"{status} {description}")
        print(f"   Command: {command}")
        print(f"   Expected: {expected}, Got: {requires_root}")
        print(f"   Root flags: {flags}")
        print()