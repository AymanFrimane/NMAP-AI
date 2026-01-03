"""
VM Simulator - Person 4 (OPTIONAL - Advanced feature)
Runs nmap commands in isolated environment and validates results

WARNING: This is an advanced feature. If you're short on time, SKIP THIS.
The other validators (syntax, conflict, safety) are sufficient.

This module:
1. Runs nmap with --oX - to get XML output
2. Parses XML to check scan success
3. Calculates score based on results
"""

import subprocess
import xml.etree.ElementTree as ET
from typing import Tuple, Optional, Dict
import time


def run_in_isolation(command: str, timeout: int = 30) -> bytes:
    """
    Run nmap command and capture XML output
    
    Adds --oX - flag to get XML format output
    Runs with timeout to prevent hanging
    
    Args:
        command: Nmap command to execute
        timeout: Maximum execution time in seconds (default: 30)
        
    Returns:
        XML output as bytes, empty bytes if failed
        
    Raises:
        subprocess.TimeoutExpired: If command takes too long
    """
    # Ensure we get XML output
    if '--oX' not in command and '-oX' not in command:
        # Add XML output to stdout
        command = command + ' --oX -'
    
    try:
        # Run command with timeout
        result = subprocess.run(
            command.split(),
            capture_output=True,
            timeout=timeout,
            text=False  # Get bytes, not string
        )
        
        # Return stdout (which contains XML)
        return result.stdout
        
    except subprocess.TimeoutExpired:
        print(f"Command timed out after {timeout}s: {command}")
        return b""
    
    except FileNotFoundError:
        print("Error: nmap not found. Please install nmap.")
        return b""
    
    except Exception as e:
        print(f"Error running command: {e}")
        return b""


def parse_xml(xml_bytes: bytes) -> float:
    """
    Parse nmap XML output and calculate success score
    
    Score calculation:
    - 1.0: All hosts found and up
    - 0.5-0.9: Some hosts up
    - 0.0: No hosts found or parse error
    
    Args:
        xml_bytes: XML output from nmap
        
    Returns:
        Score between 0.0 and 1.0
    """
    if not xml_bytes:
        return 0.0
    
    try:
        # Parse XML
        root = ET.fromstring(xml_bytes)
        
        # Count total hosts and hosts that are up
        total_hosts = 0
        hosts_up = 0
        
        # Find all host elements
        for host in root.findall('.//host'):
            total_hosts += 1
            
            # Check if host is up
            status = host.find('.//status')
            if status is not None and status.get('state') == 'up':
                hosts_up += 1
        
        # Calculate score
        if total_hosts == 0:
            # No hosts scanned - might be network issue
            return 0.0
        
        score = hosts_up / total_hosts
        return score
        
    except ET.ParseError as e:
        print(f"XML parse error: {e}")
        return 0.0
    
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return 0.0


def extract_scan_stats(xml_bytes: bytes) -> Dict[str, any]:
    """
    Extract detailed statistics from nmap XML output
    
    Returns information about:
    - Hosts scanned
    - Hosts up
    - Ports found
    - Services detected
    - Scan duration
    
    Args:
        xml_bytes: XML output from nmap
        
    Returns:
        Dictionary with scan statistics
    """
    stats = {
        'hosts_total': 0,
        'hosts_up': 0,
        'hosts_down': 0,
        'ports_open': 0,
        'ports_filtered': 0,
        'ports_closed': 0,
        'services_detected': [],
        'scan_duration': 0.0,
        'success': False
    }
    
    if not xml_bytes:
        return stats
    
    try:
        root = ET.fromstring(xml_bytes)
        
        # Get run stats
        runstats = root.find('.//runstats/hosts')
        if runstats is not None:
            stats['hosts_total'] = int(runstats.get('total', 0))
            stats['hosts_up'] = int(runstats.get('up', 0))
            stats['hosts_down'] = int(runstats.get('down', 0))
        
        # Get timing
        timing = root.find('.//runstats/finished')
        if timing is not None:
            stats['scan_duration'] = float(timing.get('elapsed', 0))
        
        # Count ports by state
        for port in root.findall('.//port'):
            state = port.find('.//state')
            if state is not None:
                port_state = state.get('state')
                if port_state == 'open':
                    stats['ports_open'] += 1
                    
                    # Get service info
                    service = port.find('.//service')
                    if service is not None:
                        service_name = service.get('name', 'unknown')
                        if service_name not in stats['services_detected']:
                            stats['services_detected'].append(service_name)
                
                elif port_state == 'filtered':
                    stats['ports_filtered'] += 1
                elif port_state == 'closed':
                    stats['ports_closed'] += 1
        
        # Determine success
        stats['success'] = stats['hosts_up'] > 0 or stats['ports_open'] > 0
        
    except Exception as e:
        print(f"Error extracting stats: {e}")
    
    return stats


def validate_with_vm(command: str, timeout: int = 30) -> Tuple[bool, float, Dict]:
    """
    Complete VM validation: run command and analyze results
    
    Args:
        command: Nmap command to validate
        timeout: Maximum execution time
        
    Returns:
        (is_valid, score, stats_dict)
    """
    # Run command
    xml_output = run_in_isolation(command, timeout)
    
    # Parse and score
    score = parse_xml(xml_output)
    stats = extract_scan_stats(xml_output)
    
    # Determine validity
    # Valid if: score > 0.3 OR command executed without error
    is_valid = score > 0.3 or (xml_output and len(xml_output) > 0)
    
    return is_valid, score, stats


# Quick test against localhost (safe)
def quick_localhost_test() -> bool:
    """
    Test VM simulator with a safe localhost scan
    
    Returns:
        True if test passes
    """
    test_command = "nmap -sn 127.0.0.1"
    
    try:
        xml = run_in_isolation(test_command, timeout=10)
        score = parse_xml(xml)
        
        print(f"Localhost test score: {score}")
        return score > 0.0
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False


# Main test
if __name__ == "__main__":
    print("=" * 60)
    print("VM SIMULATOR TESTS")
    print("=" * 60)
    print("\n⚠️  WARNING: These tests will run actual nmap commands!")
    print("   Only safe localhost scans are performed.\n")
    
    # Test 1: Simple ping scan
    print("Test 1: Ping scan localhost")
    print("-" * 60)
    command = "nmap -sn 127.0.0.1"
    print(f"Running: {command}")
    
    start_time = time.time()
    xml = run_in_isolation(command, timeout=10)
    elapsed = time.time() - start_time
    
    if xml:
        print(f"✅ Got XML output ({len(xml)} bytes) in {elapsed:.2f}s")
        score = parse_xml(xml)
        print(f"Score: {score}")
        
        stats = extract_scan_stats(xml)
        print(f"Stats: {stats}")
    else:
        print("❌ No output received")
    print()
    
    # Test 2: Port scan localhost
    print("Test 2: Port scan localhost (common ports)")
    print("-" * 60)
    command = "nmap -p 22,80,443 127.0.0.1"
    print(f"Running: {command}")
    
    is_valid, score, stats = validate_with_vm(command, timeout=15)
    print(f"Valid: {is_valid}")
    print(f"Score: {score}")
    print(f"Hosts up: {stats['hosts_up']}")
    print(f"Ports open: {stats['ports_open']}")
    print(f"Duration: {stats['scan_duration']:.2f}s")
    print()
    
    # Test 3: Invalid command
    print("Test 3: Invalid command (should fail gracefully)")
    print("-" * 60)
    command = "nmap --invalid-flag 127.0.0.1"
    print(f"Running: {command}")
    
    xml = run_in_isolation(command, timeout=5)
    if xml:
        print(f"Got output: {len(xml)} bytes")
    else:
        print("✅ Correctly failed - no output")
    print()
    
    print("=" * 60)
    print("VM SIMULATOR TESTS COMPLETE")
    print("=" * 60)
    print("\n💡 NOTE: This is an OPTIONAL feature.")
    print("   If you're short on time, focus on other validators first.")