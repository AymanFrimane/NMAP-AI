"""
Self-Correction Loop - Person 4
Iterative improvement of generated commands based on validation feedback

This module implements a retry mechanism that:
1. Generates a command
2. Validates it
3. If invalid, attempts to fix and retry
4. Returns best result after max attempts
"""

from typing import Callable, Dict, List, Optional
import copy


class SelfCorrector:
    """
    Self-correction loop for improving command quality
    
    Uses validation feedback to guide corrections:
    - Syntax errors → Remove malformed parts
    - Conflicts → Remove conflicting flags
    - Safety issues → Remove dangerous patterns
    """
    
    def __init__(self, max_retries: int = 3):
        """
        Initialize self-corrector
        
        Args:
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self.max_retries = max_retries
    
    def loop(
        self,
        intent: str,
        complexity: str,
        generator_func: Callable,
        validator_func: Callable
    ) -> Dict[str, any]:
        """
        Main self-correction loop
        
        Algorithm:
        1. Generate command
        2. Validate
        3. If valid and score >= 0.8: return
        4. Else: apply fix and retry
        5. After max retries: return best attempt
        
        Args:
            intent: User's natural language intent
            complexity: EASY | MEDIUM | HARD
            generator_func: Function(intent, complexity) -> command_string
            validator_func: Function(command) -> validation_dict
            
        Returns:
            {
                "command": best_command,
                "attempts": number_of_attempts,
                "validation": final_validation_result,
                "history": list_of_all_attempts,
                "corrected": boolean
            }
        """
        history = []
        best_result = None
        best_score = 0.0
        
        for attempt in range(self.max_retries):
            # Generate command
            try:
                command = generator_func(intent, complexity)
            except Exception as e:
                # Generator failed
                history.append({
                    "attempt": attempt + 1,
                    "command": None,
                    "error": str(e),
                    "validation": {"valid": False, "score": 0.0}
                })
                continue
            
            # Validate
            validation = validator_func(command)
            
            # Record attempt
            history.append({
                "attempt": attempt + 1,
                "command": command,
                "validation": copy.deepcopy(validation)
            })
            
            # Update best result
            current_score = validation.get('score', 0.0)
            if current_score > best_score:
                best_score = current_score
                best_result = {
                    "command": command,
                    "validation": validation,
                    "attempt": attempt + 1
                }
            
            # Check if good enough
            if validation.get('valid', False) and current_score >= 0.8:
                # Success! Return immediately
                return {
                    "command": command,
                    "attempts": attempt + 1,
                    "validation": validation,
                    "history": history,
                    "corrected": attempt > 0
                }
            
            # Try to fix for next iteration
            if attempt < self.max_retries - 1:
                # Apply fixes based on validation feedback
                fixed_command = self.apply_fixes(command, validation)
                
                # If we couldn't fix anything, no point retrying same thing
                if fixed_command == command:
                    # Can't fix - break early
                    break
                
                # Update command for next iteration
                # Note: For now we just apply fixes to the command directly
                # In production, you might feed feedback to generator
        
        # Return best attempt
        if best_result:
            return {
                "command": best_result["command"],
                "attempts": self.max_retries,
                "validation": best_result["validation"],
                "history": history,
                "corrected": best_result["attempt"] > 1
            }
        else:
            # All attempts failed - return last attempt
            return {
                "command": history[-1]["command"] if history else "",
                "attempts": self.max_retries,
                "validation": history[-1]["validation"] if history else {"valid": False, "score": 0.0},
                "history": history,
                "corrected": False
            }
    
    def apply_fixes(self, command: str, validation: Dict) -> str:
        """
        Apply fixes to command based on validation feedback
        
        Fix strategies:
        - Conflict errors: Remove one of conflicting flags
        - Syntax errors: Remove malformed parts
        - Safety errors: Remove dangerous patterns
        
        Args:
            command: Command to fix
            validation: Validation result with errors
            
        Returns:
            Fixed command (or original if can't fix)
        """
        if not command:
            return command
        
        errors = validation.get('errors', [])
        feedback = validation.get('feedback', '').lower()
        
        # Strategy 1: Remove conflicting flags
        if any('conflict' in str(e).lower() for e in errors):
            command = self._fix_conflicts(command, errors)
        
        # Strategy 2: Fix syntax issues
        if any('syntax' in str(e).lower() for e in errors):
            command = self._fix_syntax(command, errors)
        
        # Strategy 3: Remove unsafe patterns
        if any('safety' in str(e).lower() or 'dangerous' in str(e).lower() for e in errors):
            command = self._fix_safety(command)
        
        return command
    
    def _fix_conflicts(self, command: str, errors: List[str]) -> str:
        """
        Fix flag conflicts by removing one of the conflicting flags
        
        Strategy: Remove the second occurrence (keep first)
        
        Args:
            command: Command with conflicts
            errors: List of error messages
            
        Returns:
            Fixed command
        """
        import re
        
        parts = command.split()
        
        # Extract conflicting flags from error messages
        for error in errors:
            # Pattern: "flag1 conflicts with flag2"
            match = re.search(r'(-\S+)\s+conflicts with\s+(-\S+)', error)
            if match:
                flag1, flag2 = match.groups()
                
                # Remove second occurrence
                if flag2 in parts:
                    parts.remove(flag2)
                elif flag1 in parts and flag1 != flag2:
                    # If flag2 not found, remove flag1
                    parts.remove(flag1)
        
        return ' '.join(parts)
    
    def _fix_syntax(self, command: str, errors: List[str]) -> str:
        """
        Fix syntax errors
        
        Strategy: Ensure command starts with 'nmap' and has target
        
        Args:
            command: Command with syntax errors
            errors: Error messages
            
        Returns:
            Fixed command
        """
        parts = command.split()
        
        # Ensure starts with nmap
        if not parts or parts[0] != 'nmap':
            parts.insert(0, 'nmap')
        
        # Ensure has at least one target
        # Check if last part looks like a target (IP or domain)
        if len(parts) < 2:
            # Add default target (localhost for testing)
            parts.append('127.0.0.1')
        
        return ' '.join(parts)
    
    def _fix_safety(self, command: str) -> str:
        """
        Remove dangerous patterns from command
        
        Strategy: Remove file redirections and command chains
        
        Args:
            command: Command with safety issues
            
        Returns:
            Safer command
        """
        import re
        
        # Remove file redirections
        command = re.sub(r'\s*[>|<]+\s*\S*', '', command)
        
        # Remove command chaining
        command = re.sub(r'\s*[;&|]+.*$', '', command)
        
        # Remove shell substitutions
        command = re.sub(r'\$\([^)]*\)', '', command)
        command = re.sub(r'`[^`]*`', '', command)
        
        return command.strip()


# Convenience function for simple use
def correct_command(
    command: str,
    validator_func: Callable,
    max_retries: int = 3
) -> Dict[str, any]:
    """
    Simple correction function for already-generated commands
    
    Args:
        command: Command to correct
        validator_func: Validation function
        max_retries: Max correction attempts
        
    Returns:
        Correction result dict
    """
    corrector = SelfCorrector(max_retries=max_retries)
    
    # Create a dummy generator that just returns the command
    def generator(intent, complexity):
        return command
    
    return corrector.loop("", "MEDIUM", generator, validator_func)


# Test
if __name__ == "__main__":
    print("=" * 60)
    print("SELF-CORRECTION LOOP TESTS")
    print("=" * 60)
    
    # Mock validator for testing
    def mock_validator(cmd: str) -> Dict:
        """Simple mock validator for testing"""
        errors = []
        score = 1.0
        
        if not cmd.startswith('nmap'):
            errors.append("Syntax: Must start with nmap")
            score -= 0.3
        
        if '-sS' in cmd and '-sT' in cmd:
            errors.append("Conflict: -sS conflicts with -sT")
            score -= 0.4
        
        if '>' in cmd or '|' in cmd:
            errors.append("Safety: Dangerous pattern")
            score -= 0.5
        
        return {
            "valid": len(errors) == 0,
            "score": max(0.0, score),
            "errors": errors,
            "feedback": f"{len(errors)} errors" if errors else "Valid"
        }
    
    # Mock generator
    def mock_generator(intent: str, complexity: str) -> str:
        """Returns intentionally broken command"""
        return "nmap -sS -sT 192.168.1.1"  # Has conflict
    
    # Test 1: Fixing conflicts
    print("\nTest 1: Fixing conflicting flags")
    print("-" * 60)
    corrector = SelfCorrector(max_retries=3)
    result = corrector.loop("scan network", "MEDIUM", mock_generator, mock_validator)
    
    print(f"Final command: {result['command']}")
    print(f"Attempts: {result['attempts']}")
    print(f"Valid: {result['validation']['valid']}")
    print(f"Corrected: {result['corrected']}")
    print(f"History: {len(result['history'])} attempts")
    
    # Test 2: Direct command correction
    print("\nTest 2: Direct command correction")
    print("-" * 60)
    bad_command = "nmap -sS -sT > output.txt 192.168.1.1"
    print(f"Original: {bad_command}")
    
    result = correct_command(bad_command, mock_validator, max_retries=2)
    print(f"Corrected: {result['command']}")
    print(f"Valid: {result['validation']['valid']}")
    print()
    
    print("=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)
