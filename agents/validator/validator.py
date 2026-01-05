"""
Complete Validator Orchestrator - Person 4
Main validation module that coordinates all validation checks

This is your main deliverable that combines:
1. Syntax validation (syntax_checker.py)
2. Conflict detection (conflict_checker.py) 
3. Safety checks (safety_checker.py)
4. VM simulation (vm_sim.py) - OPTIONAL
5. Self-correction (self_correct.py)
6. Final decision (decision.py)
"""

from typing import Dict, Optional, Callable
import sys
import os

try:
    from agents.comprehension.classifier import get_classifier
    CLASSIFIER_AVAILABLE = True
except ImportError:
    CLASSIFIER_AVAILABLE = False

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all validation modules
try:
    from .syntax_checker import validate_syntax
    from .conflict_checker import validate_conflicts, check_requires_root
    from .safety_checker import validate_safety, get_safety_warnings, check_safe_execution
    from .self_correct import SelfCorrector
    from .decision import make_decision
except ImportError:
    # Fallback for running as script
    from syntax_checker import validate_syntax
    from conflict_checker import validate_conflicts, check_requires_root
    from safety_checker import validate_safety, get_safety_warnings, check_safe_execution
    from self_correct import SelfCorrector
    from decision import make_decision

# Optional VM simulation
try:
    from .vm_sim import validate_with_vm
    HAS_VM_SIM = True
except ImportError:
    HAS_VM_SIM = False
    print("ℹ️  VM simulation not available (optional feature)")


class CommandValidator:
    """
    Main validator that orchestrates all validation checks
    
    Usage:
        validator = CommandValidator(kg_client=kg_client)
        result = validator.full_validation("nmap -sV 192.168.1.1")
        
        if result['is_valid']:
            print(f"Command is valid with score {result['score']}")
        else:
            print(f"Errors: {result['errors']}")
    """
    
    def __init__(self, kg_client=None, use_vm_sim: bool = False):
        """
        Initialize validator
        
        Args:
            kg_client: Knowledge Graph client from P1 (for conflict checking)
            use_vm_sim: Whether to use VM simulation (default: False, it's slow)
        """
        self.kg_client = kg_client
        self.use_vm_sim = use_vm_sim and HAS_VM_SIM
        
        if use_vm_sim and not HAS_VM_SIM:
            print("⚠️  VM simulation requested but not available")
    
    def full_validation(self, command: str) -> Dict[str, any]:
        """
        Run complete validation pipeline
        
        Steps:
        1. Syntax check
        2. Conflict detection (via KG if available)
        3. Safety check
        4. VM simulation (if enabled and all above pass)
        5. Aggregate results
        
        Args:
            command: Nmap command to validate
            
        Returns:
            {
                "is_valid": bool,
                "score": float (0-1),
                "feedback": str,
                "errors": list of error messages,
                "warnings": list of warnings,
                "details": dict with individual check results
            }
        """
        errors = []
        warnings = []
        score = 1.0
        details = {}
        
        # Step 1: Syntax validation
        syntax_valid, syntax_msg = validate_syntax(command)
        details['syntax'] = {"valid": syntax_valid, "message": syntax_msg}
        
        if not syntax_valid:
            errors.append(f"Syntax: {syntax_msg}")
            score -= 0.3
        
        # Step 2: Conflict detection
        conflict_valid, conflict_msg = validate_conflicts(command, self.kg_client)
        details['conflicts'] = {"valid": conflict_valid, "message": conflict_msg}
        
        if not conflict_valid:
            errors.append(f"Conflict: {conflict_msg}")
            score -= 0.4
        
        # Step 3: Safety check
        safety_valid, safety_errors, safety_warnings = check_safe_execution(command)
        details['safety'] = {
            "valid": safety_valid,
            "errors": safety_errors,
            "warnings": safety_warnings
        }
        
        if not safety_valid:
            errors.extend([f"Safety: {e}" for e in safety_errors])
            score -= 0.5
        
        warnings.extend(safety_warnings)
        
        # Step 4: Check root requirement
        requires_root, root_flags = check_requires_root(command, self.kg_client)
        details['root'] = {"required": requires_root, "flags": root_flags}
        
        if requires_root:
            warnings.append(f"Requires root privileges for: {', '.join(root_flags)}")
        
        # Step 5: VM simulation (optional, only if syntax valid and no errors)
        if self.use_vm_sim and syntax_valid and len(errors) == 0:
            try:
                vm_valid, vm_score, vm_stats = validate_with_vm(command, timeout=30)
                details['vm'] = {
                    "valid": vm_valid,
                    "score": vm_score,
                    "stats": vm_stats
                }
                
                # Average score with VM result
                score = (score + vm_score) / 2
                
                if vm_score < 0.5:
                    warnings.append(f"Low VM validation score: {vm_score:.2f}")
                    
            except Exception as e:
                warnings.append(f"VM simulation failed: {str(e)}")
                details['vm'] = {"error": str(e)}
        
        # Calculate final score (ensure in range 0-1)
        score = max(0.0, min(1.0, score))
        
        # Determine overall validity
        is_valid = len(errors) == 0 and score >= 0.5
        
        # Generate feedback
        if is_valid:
            if warnings:
                feedback = f"Valid command with {len(warnings)} warning(s)"
            else:
                feedback = "Command is valid and safe"
        else:
            feedback = f"Command has {len(errors)} error(s)"
        
        return {
            "is_valid": is_valid,
            "score": score,
            "feedback": feedback,
            "errors": errors,
            "warnings": warnings,
            "details": details
        }
    
    def quick_validation(self, command: str) -> bool:
        """
        Fast validation check (syntax + safety only, no KG)
        
        Use this for quick checks when speed matters more than thoroughness
        
        Args:
            command: Nmap command
            
        Returns:
            True if passes basic checks
        """
        syntax_valid, _ = validate_syntax(command)
        safety_valid = validate_safety(command)
        
        return syntax_valid and safety_valid
    
    def validate_and_suggest(self, command: str) -> Dict[str, any]:
        """
        Validate command and suggest improvements
        
        Args:
            command: Nmap command
            
        Returns:
            Validation result with suggestions
        """
        result = self.full_validation(command)
        
        # Add suggestions based on errors
        suggestions = []
        
        for error in result['errors']:
            if 'conflict' in error.lower():
                suggestions.append("Remove one of the conflicting flags")
            elif 'syntax' in error.lower():
                suggestions.append("Check command format: nmap [options] [target]")
            elif 'safety' in error.lower():
                suggestions.append("Remove dangerous patterns like >, |, ;")
        
        result['suggestions'] = suggestions
        return result
    
    def get_complexity_from_nl(self, natural_language_query: str):
        """Get complexity from natural language query (uses P1's classifier)"""
        if not CLASSIFIER_AVAILABLE:
            return None
    
        try:
            classifier = get_classifier()
            result = classifier.comprehend(natural_language_query)
            return result.get('complexity')
        except Exception as e:
            print(f"Classifier error: {e}")
            return None


class ValidationPipeline:
    """
    Complete validation pipeline with self-correction and decision
    
    This combines:
    - Validation (CommandValidator)
    - Self-correction (SelfCorrector)
    - Final decision (make_decision)
    """
    
    def __init__(self, kg_client=None, max_retries: int = 3):
        """
        Initialize pipeline
        
        Args:
            kg_client: Knowledge Graph client
            max_retries: Max self-correction attempts
        """
        self.validator = CommandValidator(kg_client=kg_client)
        self.corrector = SelfCorrector(max_retries=max_retries)
    
    def process(
        self,
        intent: str,
        complexity: str,
        generator_func: Callable
    ) -> Dict[str, any]:
        """
        Complete pipeline: generate → validate → correct → decide
        
        Args:
            intent: User's natural language intent
            complexity: EASY | MEDIUM | HARD
            generator_func: Function that generates commands
            
        Returns:
            Final decision with command, confidence, explanation
        """
        # Self-correction loop
        correction_result = self.corrector.loop(
            intent=intent,
            complexity=complexity,
            generator_func=generator_func,
            validator_func=self.validator.full_validation
        )
        
        # Make final decision
        decision = make_decision(
            command=correction_result['command'],
            validation=correction_result['validation'],
            generation_info={
                'complexity': complexity,
                'attempts': correction_result['attempts'],
                'corrected': correction_result['corrected']
            }
        )
        
        # Add correction history
        decision['correction_history'] = correction_result['history']
        
        return decision


# Convenience function for simple use
def validate_command(command: str, kg_client=None) -> Dict[str, any]:
    """
    Simple validation function
    
    Args:
        command: Nmap command to validate
        kg_client: Optional KG client
        
    Returns:
        Validation result
    """
    validator = CommandValidator(kg_client=kg_client)
    return validator.full_validation(command)


# Test
if __name__ == "__main__":
    print("=" * 70)
    print("COMPLETE VALIDATOR ORCHESTRATOR TESTS")
    print("=" * 70)
    
    # Initialize validator
    validator = CommandValidator(kg_client=None, use_vm_sim=False)
    
    # Test cases
    test_commands = [
        ("nmap -sV -p 80,443 192.168.1.1", "Valid command"),
        ("nmap -sS -sT 192.168.1.1", "Conflicting scan types"),
        ("nmap > output.txt 192.168.1.1", "File redirection (unsafe)"),
        ("scan 192.168.1.1", "Invalid syntax (no 'nmap')"),
        ("nmap -sU 192.168.1.1", "UDP scan (requires root)"),
        ("nmap --script vuln -T5 192.168.1.0/24", "Aggressive with warnings"),
    ]
    
    print("\n" + "=" * 70)
    print("Running validation tests...")
    print("=" * 70 + "\n")
    
    for i, (cmd, description) in enumerate(test_commands, 1):
        print(f"Test {i}: {description}")
        print("-" * 70)
        print(f"Command: {cmd}")
        
        result = validator.full_validation(cmd)
        
        print(f"Valid: {result['is_valid']}")
        print(f"Score: {result['score']:.2f}")
        print(f"Feedback: {result['feedback']}")
        
        if result['errors']:
            print(f"Errors ({len(result['errors'])}):")
            for error in result['errors']:
                print(f"  ❌ {error}")
        
        if result['warnings']:
            print(f"Warnings ({len(result['warnings'])}):")
            for warning in result['warnings'][:3]:  # Show first 3
                print(f"  ⚠️  {warning}")
        
        print()
    
    # Test quick validation
    print("=" * 70)
    print("Quick validation test (fast path)")
    print("=" * 70 + "\n")
    
    quick_tests = [
        "nmap -sV 192.168.1.1",
        "invalid command",
        "nmap > file.txt 192.168.1.1"
    ]
    
    for cmd in quick_tests:
        quick_result = validator.quick_validation(cmd)
        print(f"{'✅' if quick_result else '❌'} {cmd[:50]}")
    
    print("\n" + "=" * 70)
    print("VALIDATOR ORCHESTRATOR READY FOR PRODUCTION! 🚀")
    print("=" * 70)
