"""
Validator Package - Person 4
Command validation, conflict detection, safety checks, and self-correction
"""

from .validator import CommandValidator, ValidationPipeline
from .syntax_checker import validate_syntax, quick_syntax_check
from .conflict_checker import validate_conflicts, extract_flags, check_requires_root
from .safety_checker import validate_safety, check_safe_execution, get_safety_warnings
from .self_correct import SelfCorrector, correct_command
from .decision import make_decision, calculate_confidence

__all__ = [
    # Main classes
    'CommandValidator',
    'ValidationPipeline',
    'SelfCorrector',
    
    # Syntax validation
    'validate_syntax',
    'quick_syntax_check',
    
    # Conflict detection
    'validate_conflicts',
    'extract_flags',
    'check_requires_root',
    
    # Safety checks
    'validate_safety',
    'check_safe_execution',
    'get_safety_warnings',
    
    # Self-correction
    'correct_command',
    
    # Decision making
    'make_decision',
    'calculate_confidence',
]

__version__ = '1.0.0'
__author__ = 'Person 4 - NMAP-AI Team'