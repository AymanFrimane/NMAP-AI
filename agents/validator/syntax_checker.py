"""
Syntax Checker - Person 4
Validates nmap command syntax without executing it
"""

import re
import subprocess
from typing import Tuple


# Known nmap flags for basic validation
KNOWN_FLAGS = {
    # Scan types
    '-sS', '-sT', '-sU', '-sn', '-sA', '-sW', '-sN', '-sF', '-sX',
    # Port specification
    '-p', '-p-', '--exclude-ports',
    # Detection
    '-sV', '-O', '-A',
    # Timing
    '-T0', '-T1', '-T2', '-T3', '-T4', '-T5',
    # Host discovery
    '-Pn', '-PS', '-PA', '-PU', '-PE', '-PP', '-PM',
    # Output
    '-oN', '-oX', '-oG', '-oA', '-v', '-vv',
    # Other
    '-6', '-n', '-R', '--traceroute', '--reason', '--open',
    # Scripts
    '--script', '--script-args',
}


def validate_syntax(command: str) -> Tuple[bool, str]:
    """
    Validate nmap command syntax
    
    Checks:
    1. Command starts with 'nmap'
    2. Has at least a target
    3. Flags are well-formed
    4. Target IP/domain is valid format
    
    Args:
        command: Nmap command string
        
    Returns:
        (is_valid, feedback_message)
    """
    # 1. Check starts with nmap
    command = command.strip()
    if not command.startswith('nmap'):
        return False, "Command must start with 'nmap'"
    
    # 2. Split and check length
    parts = command.split()
    if len(parts) < 2:
        return False, "Command too short - missing target"
    
    # 3. Extract flags and target
    flags = []
    targets = []
    
    for i, part in enumerate(parts[1:], 1):  # Skip 'nmap'
        if part.startswith('-'):
            flags.append(part)
        else:
            # Could be target or flag argument
            if i > 1 and parts[i-1].startswith('-'):
                # Argument to previous flag
                continue
            targets.append(part)
    
    # 4. Must have at least one target
    if not targets:
        return False, "No target specified"
    
    # 5. Validate target format (basic check)
    for target in targets:
        if not _is_valid_target(target):
            return False, f"Invalid target format: {target}"
    
    # 6. Check for common syntax errors
    for flag in flags:
        # Check double dashes are intentional
        if flag.startswith('--') and not _is_long_flag(flag):
            return False, f"Invalid long flag: {flag}"
        
        # Check single dash flags
        if flag.startswith('-') and not flag.startswith('--'):
            if len(flag) > 3 and not flag[1:].replace('-', '').isdigit():
                # Flags like -T4 are OK, but -sSSS is not
                base_flag = flag[:2] if len(flag) >= 2 else flag
                if base_flag not in KNOWN_FLAGS:
                    return False, f"Unknown or malformed flag: {flag}"
    
    # 7. Use nmap --help to validate (optional, slower)
    # This can be skipped for performance
    # if not _validate_with_nmap(command):
    #     return False, "Command rejected by nmap --help"
    
    return True, "Syntax valid"


def _is_valid_target(target: str) -> bool:
    """Check if target is valid IP, CIDR, or domain"""
    # IP address (simple check)
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(ip_pattern, target):
        # Check each octet is 0-255
        octets = target.split('.')
        return all(0 <= int(o) <= 255 for o in octets)
    
    # CIDR notation
    cidr_pattern = r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$'
    if re.match(cidr_pattern, target):
        ip_part = target.split('/')[0]
        cidr_part = int(target.split('/')[1])
        return _is_valid_target(ip_part) and 0 <= cidr_part <= 32
    
    # Domain name (basic check)
    domain_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    if re.match(domain_pattern, target):
        return True
    
    # Hostname (single word)
    if re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$', target):
        return True
    
    return False


def _is_long_flag(flag: str) -> bool:
    """Check if double-dash flag is valid"""
    known_long_flags = [
        '--script', '--script-args', '--traceroute', '--reason',
        '--exclude-ports', '--port-ratio', '--version-intensity',
        '--osscan-limit', '--max-retries', '--host-timeout',
        '--open', '--version-all', '--version-light'
    ]
    
    # Exact match
    if flag in known_long_flags:
        return True
    
    # Prefix match (for flags with arguments like --script=default)
    for known in known_long_flags:
        if flag.startswith(known):
            return True
    
    return False


def _validate_with_nmap(command: str) -> bool:
    """
    Optional: Validate using nmap --help
    This is slower but more accurate
    
    Args:
        command: Command to validate
        
    Returns:
        True if nmap accepts the syntax
    """
    try:
        # Run nmap with --help to check if flags are valid
        # This doesn't execute the scan
        result = subprocess.run(
            ['nmap', '--help'],
            capture_output=True,
            timeout=5
        )
        
        # Parse help output to check flags
        help_text = result.stdout.decode()
        
        # Extract flags from command
        flags = re.findall(r'-[a-zA-Z0-9]+|--[\w-]+', command)
        
        # Check each flag appears in help
        for flag in flags:
            # Remove any arguments (e.g., --script=default -> --script)
            flag_base = flag.split('=')[0]
            if flag_base not in help_text:
                return False
        
        return True
        
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # If nmap not available or times out, return True
        # (we did basic checks already)
        return True


# Quick validation for common mistakes
def quick_syntax_check(command: str) -> bool:
    """
    Ultra-fast syntax check (just the basics)
    
    Args:
        command: Nmap command
        
    Returns:
        True if passes basic checks
    """
    return (
        command.strip().startswith('nmap') and
        len(command.split()) >= 2
    )


if __name__ == "__main__":
    # Test cases
    test_commands = [
        ("nmap -sV -p 80,443 192.168.1.1", True),
        ("nmap 192.168.1.0/24", True),
        ("nmap -p- example.com", True),
        ("scan 192.168.1.1", False),  # Doesn't start with nmap
        ("nmap", False),  # No target
        ("nmap -sSSS 192.168.1.1", False),  # Malformed flag
        ("nmap 999.999.999.999", False),  # Invalid IP
    ]
    
    print("Testing syntax checker...")
    for cmd, expected in test_commands:
        valid, msg = validate_syntax(cmd)
        status = "✅" if valid == expected else "❌"
        print(f"{status} {cmd[:50]:50} -> {valid} ({msg})")
