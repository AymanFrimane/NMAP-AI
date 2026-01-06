"""
Safety Checker - Person 4
Detects dangerous patterns and blacklisted commands in nmap commands

Prevents:
- File operations (>, >>, <, |)
- Shell command injection (;, &&, ||, $)
- Dangerous scripts (exploit, vuln without caution)
- System modifications (rm, chmod, sudo in command)
"""

import re
from typing import List, Tuple


# Blacklisted patterns that indicate dangerous operations
BLACKLIST_PATTERNS = [
    # File redirection and piping
    '>',      # Output redirection
    '>>',     # Append redirection
    '<',      # Input redirection
    '|',      # Pipe to another command
    
    # Command chaining (command injection)
    ';',      # Command separator
    '&&',     # AND operator
    '||',     # OR operator
    '`',      # Command substitution
    '$(',     # Command substitution
    
    # Dangerous system commands
    'rm ',    # Remove files
    'chmod ', # Change permissions
    'chown ', # Change ownership
    'dd ',    # Disk operations
    'mkfs',   # Format filesystem
    
    # Dangerous nmap scripts (allow with warning)
    # These are checked separately with warnings
]

# Scripts that should generate warnings but not block
WARNING_SCRIPTS = [
    'exploit',  # Exploitation scripts
    'dos',      # Denial of service
    'brute',    # Brute force
    'broadcast',  # Broadcast scripts
]

# Completely forbidden scripts
FORBIDDEN_SCRIPTS = [
    'malware',  # Malware scripts are too dangerous
]


def validate_safety(command: str) -> bool:
    """
    Check if command is safe to execute
    
    Blocks commands that:
    - Contain file operations
    - Use command chaining
    - Include dangerous system commands
    - Use forbidden scripts
    
    Args:
        command: Nmap command to check
        
    Returns:
        True if safe, False if dangerous
    """
    command_lower = command.lower()
    
    # Check blacklist patterns
    for pattern in BLACKLIST_PATTERNS:
        if pattern in command:
            return False
    
    # Check for forbidden scripts
    if '--script' in command_lower:
        for forbidden in FORBIDDEN_SCRIPTS:
            if forbidden in command_lower:
                return False
    
    return True


def get_safety_warnings(command: str) -> List[str]:
    """
    Get list of safety warnings (not blocking, but user should know)
    
    Warnings for:
    - Aggressive scan options
    - Potentially noisy scripts
    - High-risk operations
    
    Args:
        command: Nmap command
        
    Returns:
        List of warning messages
    """
    warnings = []
    command_lower = command.lower()
    
    # Check for warning-level scripts
    if '--script' in command_lower:
        for script in WARNING_SCRIPTS:
            if script in command_lower:
                warnings.append(f"Script category '{script}' may be aggressive")
    
    # Check for aggressive timing
    if '-T4' in command or '-T5' in command:
        warnings.append("Aggressive timing (-T4/-T5) may be detected")
    
    # Check for aggressive scan type
    if '-A' in command:
        warnings.append("Aggressive scan (-A) enables OS detection and scripts")
    
    # Check for full port scan
    if '-p-' in command or '-p 1-65535' in command:
        warnings.append("Full port scan will take significant time")
    
    # Check for UDP scan
    if '-sU' in command:
        warnings.append("UDP scan requires root and is slower")
    
    # Check for version detection
    if '-sV' in command:
        warnings.append("Version detection increases scan time")
    
    # Check for OS detection
    if '-O' in command:
        warnings.append("OS detection requires root privileges")
    
    # Check for script scan
    if '--script' in command_lower and 'vuln' in command_lower:
        warnings.append("Vulnerability scripts may trigger IDS/IPS")
    
    return warnings


def check_safe_execution(command: str) -> Tuple[bool, List[str], List[str]]:
    """
    Complete safety check with errors and warnings
    
    Args:
        command: Nmap command
        
    Returns:
        (is_safe, list_of_errors, list_of_warnings)
    """
    errors = []
    warnings = []
    
    # Check for blocking issues
    if not validate_safety(command):
        # Identify which patterns caused the block
        command_lower = command.lower()
        
        for pattern in BLACKLIST_PATTERNS:
            if pattern in command:
                errors.append(f"Dangerous pattern detected: {pattern}")
        
        if '--script' in command_lower:
            for forbidden in FORBIDDEN_SCRIPTS:
                if forbidden in command_lower:
                    errors.append(f"Forbidden script: {forbidden}")
    
    # Get warnings
    warnings = get_safety_warnings(command)
    
    is_safe = len(errors) == 0
    
    return is_safe, errors, warnings


def sanitize_command(command: str) -> str:
    """
    Attempt to sanitize a command by removing dangerous parts
    
    This is a simple approach - just removes obvious dangerous patterns.
    For production, more sophisticated sanitization would be needed.
    
    Args:
        command: Potentially unsafe command
        
    Returns:
        Sanitized command (or original if cannot sanitize)
    """
    # Remove file redirections
    command = re.sub(r'\s*[>|<]+\s*\S*', '', command)
    
    # Remove command chaining
    command = re.sub(r'\s*[;&|]+\s*', ' ', command)
    
    # Remove shell substitutions
    command = re.sub(r'\$\([^)]*\)', '', command)
    command = re.sub(r'`[^`]*`', '', command)
    
    return command.strip()


# Test function
if __name__ == "__main__":
    print("=" * 60)
    print("SAFETY CHECKER TESTS")
    print("=" * 60)
    
    test_cases = [
        # (command, expected_safe, description)
        ("nmap -sV -p 80,443 192.168.1.1", True, "Normal scan - SAFE"),
        ("nmap 192.168.1.1 > output.txt", False, "File redirection - BLOCKED"),
        ("nmap 192.168.1.1 | grep open", False, "Pipe to grep - BLOCKED"),
        ("nmap 192.168.1.1; rm -rf /", False, "Command injection - BLOCKED"),
        ("nmap -sS 192.168.1.1 && echo done", False, "Command chaining - BLOCKED"),
        ("nmap --script vuln 192.168.1.1", True, "Vuln script - SAFE but WARNING"),
        ("nmap --script malware 192.168.1.1", False, "Malware script - BLOCKED"),
        ("nmap -T5 -p- 192.168.1.1", True, "Aggressive scan - SAFE but WARNING"),
        ("nmap -A 192.168.1.1", True, "Aggressive mode - SAFE but WARNING"),
        ("sudo nmap -sS 192.168.1.1", False, "Contains 'sudo' - BLOCKED"),
    ]
    
    print("\nTesting validate_safety():")
    print("-" * 60)
    for cmd, expected, description in test_cases:
        result = validate_safety(cmd)
        status = "✅" if result == expected else "❌"
        print(f"{status} {description}")
        print(f"   Command: {cmd[:60]}")
        print(f"   Result: {'SAFE' if result else 'BLOCKED'}")
        print()
    
    print("\nTesting check_safe_execution() with warnings:")
    print("-" * 60)
    for cmd, _, description in test_cases[:5]:  # First 5 examples
        is_safe, errors, warnings = check_safe_execution(cmd)
        print(f"Command: {cmd[:60]}")
        print(f"Safe: {is_safe}")
        if errors:
            print(f"Errors: {errors}")
        if warnings:
            print(f"Warnings: {warnings}")
        print()
    
    print("\nTesting sanitize_command():")
    print("-" * 60)
    dangerous_commands = [
        "nmap 192.168.1.1 > out.txt",
        "nmap 192.168.1.1 | grep open",
        "nmap 192.168.1.1; echo done",
    ]
    for cmd in dangerous_commands:
        sanitized = sanitize_command(cmd)
        print(f"Original:  {cmd}")
        print(f"Sanitized: {sanitized}")
        print(f"Now safe:  {validate_safety(sanitized)}")
        print()
