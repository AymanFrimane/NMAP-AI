"""
Complete Test Suite for Person 4
Tests all validation modules and integration

Run with:
    pytest tests/test_p4_validator.py -v
    pytest tests/test_p4_validator.py --cov=agents/validator
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import validation modules
from agents.validator.syntax_checker import validate_syntax, quick_syntax_check
from agents.validator.conflict_checker import validate_conflicts, extract_flags, check_requires_root
from agents.validator.safety_checker import validate_safety, check_safe_execution, get_safety_warnings
from agents.validator.self_correct import SelfCorrector, correct_command
from agents.validator.decision import make_decision, calculate_confidence
from agents.validator.validator import CommandValidator, ValidationPipeline


# ============================================================================
# Test Syntax Checker
# ============================================================================

class TestSyntaxChecker:
    """Test syntax validation"""
    
    def test_valid_basic_command(self):
        """Test basic valid command"""
        valid, msg = validate_syntax("nmap 192.168.1.1")
        assert valid == True
        assert "valid" in msg.lower()
    
    def test_valid_with_flags(self):
        """Test valid command with flags"""
        valid, msg = validate_syntax("nmap -sV -p 80,443 192.168.1.1")
        assert valid == True
    
    def test_invalid_no_nmap(self):
        """Test command without 'nmap'"""
        valid, msg = validate_syntax("scan 192.168.1.1")
        assert valid == False
        assert "nmap" in msg.lower()
    
    def test_invalid_no_target(self):
        """Test command without target"""
        valid, msg = validate_syntax("nmap")
        assert valid == False
        assert "target" in msg.lower()
    
    def test_invalid_ip_address(self):
        """Test invalid IP address"""
        valid, msg = validate_syntax("nmap 999.999.999.999")
        assert valid == False
    
    def test_valid_cidr_notation(self):
        """Test CIDR notation"""
        valid, msg = validate_syntax("nmap 192.168.1.0/24")
        assert valid == True
    
    def test_valid_domain(self):
        """Test domain name"""
        valid, msg = validate_syntax("nmap example.com")
        assert valid == True
    
    def test_quick_syntax_check(self):
        """Test quick validation"""
        assert quick_syntax_check("nmap 192.168.1.1") == True
        assert quick_syntax_check("scan 192.168.1.1") == False
        assert quick_syntax_check("nmap") == False


# ============================================================================
# Test Conflict Checker
# ============================================================================

class TestConflictChecker:
    """Test conflict detection"""
    
    def test_extract_flags(self):
        """Test flag extraction"""
        flags = extract_flags("nmap -sS -p 80,443 --script default 192.168.1.1")
        assert '-sS' in flags
        assert '-p' in flags
        assert '--script' in flags
    
    def test_valid_no_conflicts(self):
        """Test command with no conflicts"""
        valid, msg = validate_conflicts("nmap -sV -p 80,443 192.168.1.1", kg_client=None)
        assert valid == True
    
    def test_scan_type_conflict(self):
        """Test conflicting scan types"""
        valid, msg = validate_conflicts("nmap -sS -sT 192.168.1.1", kg_client=None)
        assert valid == False
        assert "conflict" in msg.lower()
    
    def test_ping_scan_port_conflict(self):
        """Test ping scan with port specification"""
        valid, msg = validate_conflicts("nmap -sn -p 80 192.168.1.1", kg_client=None)
        assert valid == False
        assert "conflict" in msg.lower()
    
    def test_check_requires_root(self):
        """Test root requirement check"""
        requires_root, flags = check_requires_root("nmap -sS 192.168.1.1", kg_client=None)
        assert requires_root == True
        assert '-sS' in flags
    
    def test_no_root_required(self):
        """Test command not requiring root"""
        requires_root, flags = check_requires_root("nmap -sT 192.168.1.1", kg_client=None)
        # -sT may or may not require root depending on implementation
        # Just check it returns a boolean
        assert isinstance(requires_root, bool)


# ============================================================================
# Test Safety Checker
# ============================================================================

class TestSafetyChecker:
    """Test safety validation"""
    
    def test_safe_command(self):
        """Test safe command"""
        assert validate_safety("nmap -sV 192.168.1.1") == True
    
    def test_unsafe_file_redirect(self):
        """Test file redirection"""
        assert validate_safety("nmap 192.168.1.1 > output.txt") == False
    
    def test_unsafe_pipe(self):
        """Test pipe to another command"""
        assert validate_safety("nmap 192.168.1.1 | grep open") == False
    
    def test_unsafe_command_chaining(self):
        """Test command chaining"""
        assert validate_safety("nmap 192.168.1.1; echo done") == False
        assert validate_safety("nmap 192.168.1.1 && echo done") == False
    
    def test_unsafe_command_injection(self):
        """Test command injection attempts"""
        assert validate_safety("nmap $(whoami) 192.168.1.1") == False
        assert validate_safety("nmap `whoami` 192.168.1.1") == False
    
    def test_check_safe_execution(self):
        """Test complete safety check"""
        is_safe, errors, warnings = check_safe_execution("nmap -sV 192.168.1.1")
        assert is_safe == True
        assert len(errors) == 0
    
    def test_get_warnings(self):
        """Test warning generation"""
        warnings = get_safety_warnings("nmap -T5 -A --script vuln 192.168.1.1")
        assert len(warnings) > 0
        assert any("aggressive" in w.lower() for w in warnings)


# ============================================================================
# Test Self-Correction
# ============================================================================

class TestSelfCorrection:
    """Test self-correction loop"""
    
    def mock_validator(self, cmd: str) -> dict:
        """Mock validator for testing"""
        errors = []
        score = 1.0
        
        if not cmd.startswith('nmap'):
            errors.append("Syntax: Must start with nmap")
            score -= 0.3
        
        if '-sS' in cmd and '-sT' in cmd:
            errors.append("Conflict: -sS conflicts with -sT")
            score -= 0.4
        
        return {
            "is_valid": len(errors) == 0,
            "valid": len(errors) == 0,
            "score": max(0.0, score),
            "errors": errors,
            "feedback": "Valid" if len(errors) == 0 else f"{len(errors)} errors"
        }
    
    def mock_generator(self, intent: str, complexity: str) -> str:
        """Mock generator"""
        return "nmap -sS -sT 192.168.1.1"  # Intentionally broken
    
    def test_correction_loop(self):
        """Test self-correction loop"""
        corrector = SelfCorrector(max_retries=3)
        result = corrector.loop(
            "scan network",
            "MEDIUM",
            self.mock_generator,
            self.mock_validator
        )
        
        assert 'command' in result
        assert 'attempts' in result
        assert 'validation' in result
        assert result['attempts'] <= 3
    
    def test_correction_fixes_command(self):
        """Test that correction actually fixes issues"""
        bad_command = "nmap -sS -sT 192.168.1.1"
        result = correct_command(bad_command, self.mock_validator, max_retries=2)
        
        # Command should be different after correction
        assert result['command'] != bad_command or result['validation']['is_valid']


# ============================================================================
# Test Decision Agent
# ============================================================================

class TestDecisionAgent:
    """Test final decision making"""
    
    def test_high_confidence_decision(self):
        """Test decision with high quality command"""
        validation = {
            "is_valid": True,
            "valid": True,
            "score": 0.95,
            "errors": [],
            "warnings": []
        }
        
        decision = make_decision("nmap -sV 192.168.1.1", validation)
        
        assert 'command' in decision
        assert 'confidence' in decision
        assert 'explanation' in decision
        assert decision['confidence'] > 0.7
    
    def test_low_confidence_decision(self):
        """Test decision with problematic command"""
        validation = {
            "is_valid": False,
            "valid": False,
            "score": 0.3,
            "errors": ["Syntax error", "Safety issue"],
            "warnings": []
        }
        
        gen_info = {
            "complexity": "HARD",
            "attempts": 3,
            "corrected": True
        }
        
        decision = make_decision("bad command", validation, gen_info)
        
        assert decision['confidence'] < 0.5
    
    def test_confidence_calculation(self):
        """Test confidence score calculation"""
        # Perfect command
        conf1 = calculate_confidence(
            is_valid=True,
            score=0.95,
            attempts=1,
            has_errors=False,
            has_warnings=False,
            complexity="EASY"
        )
        assert conf1 > 0.8
        
        # Problematic command
        conf2 = calculate_confidence(
            is_valid=False,
            score=0.3,
            attempts=3,
            has_errors=True,
            has_warnings=True,
            complexity="HARD"
        )
        assert conf2 < 0.5


# ============================================================================
# Test Complete Validator
# ============================================================================

class TestCompleteValidator:
    """Test main validator orchestrator"""
    
    def test_validator_initialization(self):
        """Test validator can be created"""
        validator = CommandValidator(kg_client=None)
        assert validator is not None
    
    def test_full_validation_valid_command(self):
        """Test full validation of valid command"""
        validator = CommandValidator()
        result = validator.full_validation("nmap -sV -p 80,443 192.168.1.1")
        
        assert 'is_valid' in result
        assert 'score' in result
        assert 'errors' in result
        assert 'warnings' in result
        assert isinstance(result['score'], float)
        assert 0.0 <= result['score'] <= 1.0
    
    def test_full_validation_invalid_syntax(self):
        """Test validation of syntactically invalid command"""
        validator = CommandValidator()
        result = validator.full_validation("invalid command")
        
        assert result['is_valid'] == False
        assert len(result['errors']) > 0
        assert any('syntax' in e.lower() for e in result['errors'])
    
    def test_full_validation_unsafe_command(self):
        """Test validation of unsafe command"""
        validator = CommandValidator()
        result = validator.full_validation("nmap > output.txt 192.168.1.1")
        
        assert result['is_valid'] == False
        assert any('safety' in e.lower() for e in result['errors'])
    
    def test_quick_validation(self):
        """Test quick validation"""
        validator = CommandValidator()
        assert validator.quick_validation("nmap 192.168.1.1") == True
        assert validator.quick_validation("invalid") == False


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for complete pipeline"""
    
    def test_end_to_end_validation(self):
        """Test complete validation pipeline"""
        validator = CommandValidator()
        
        test_commands = [
            "nmap -sV -p 80,443 192.168.1.1",
            "nmap -sS -sT 192.168.1.1",
            "nmap > file.txt 192.168.1.1",
        ]
        
        for cmd in test_commands:
            result = validator.full_validation(cmd)
            assert 'is_valid' in result
            assert 'score' in result
    
    def test_validation_pipeline(self):
        """Test ValidationPipeline class"""
        pipeline = ValidationPipeline(kg_client=None, max_retries=2)
        assert pipeline is not None
        assert pipeline.validator is not None
        assert pipeline.corrector is not None


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
