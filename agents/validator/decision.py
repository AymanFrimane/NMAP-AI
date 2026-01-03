"""
Final Decision Agent - Person 4
Calculates confidence scores and generates explanations for final commands

This is the last step in the pipeline:
1. Command has been generated
2. Command has been validated
3. Self-correction has been applied (if needed)
4. Now we calculate confidence and provide explanation
"""

from typing import Dict, List, Optional


def make_decision(
    command: str,
    validation: Dict,
    generation_info: Optional[Dict] = None
) -> Dict[str, any]:
    """
    Make final decision with confidence score and explanation
    
    Confidence calculation:
    - Base: 0.7
    - +0.2 if validation score is high (>0.8)
    - +0.1 if no warnings
    - -0.1 per retry attempt
    - -0.2 if validation has errors
    
    Args:
        command: Final command string
        validation: Validation result dict
        generation_info: Optional dict with:
            - complexity: EASY | MEDIUM | HARD
            - attempts: number of retry attempts
            - corrected: whether command was corrected
            
    Returns:
        {
            "command": str,
            "confidence": float (0-1),
            "explanation": str,
            "validation": dict,
            "metadata": dict
        }
    """
    # Extract validation info
    is_valid = validation.get('valid', False)
    score = validation.get('score', 0.0)
    errors = validation.get('errors', [])
    warnings = validation.get('warnings', [])
    
    # Extract generation info
    if generation_info is None:
        generation_info = {}
    
    complexity = generation_info.get('complexity', 'MEDIUM')
    attempts = generation_info.get('attempts', 1)
    corrected = generation_info.get('corrected', False)
    
    # Calculate confidence
    confidence = calculate_confidence(
        is_valid=is_valid,
        score=score,
        attempts=attempts,
        has_errors=len(errors) > 0,
        has_warnings=len(warnings) > 0,
        complexity=complexity
    )
    
    # Generate explanation
    explanation = generate_explanation(
        command=command,
        is_valid=is_valid,
        score=score,
        errors=errors,
        warnings=warnings,
        complexity=complexity,
        attempts=attempts,
        corrected=corrected
    )
    
    # Create metadata
    metadata = {
        "complexity": complexity,
        "attempts": attempts,
        "corrected": corrected,
        "validation_score": score,
        "has_errors": len(errors) > 0,
        "has_warnings": len(warnings) > 0
    }
    
    return {
        "command": command,
        "confidence": confidence,
        "explanation": explanation,
        "validation": validation,
        "metadata": metadata
    }


def calculate_confidence(
    is_valid: bool,
    score: float,
    attempts: int,
    has_errors: bool,
    has_warnings: bool,
    complexity: str
) -> float:
    """
    Calculate confidence score based on multiple factors
    
    Formula:
    - Start with base 0.7
    - Add/subtract based on validation
    - Adjust for complexity and attempts
    
    Args:
        is_valid: Whether command passed validation
        score: Validation score (0-1)
        attempts: Number of generation attempts
        has_errors: Whether validation found errors
        has_warnings: Whether validation found warnings
        complexity: EASY | MEDIUM | HARD
        
    Returns:
        Confidence score between 0 and 1
    """
    # Base confidence
    confidence = 0.7
    
    # Factor 1: Validation score (most important)
    if is_valid and score >= 0.9:
        confidence += 0.2  # Excellent validation
    elif is_valid and score >= 0.7:
        confidence += 0.1  # Good validation
    elif is_valid:
        confidence += 0.05  # Minimal validation
    else:
        confidence -= 0.2  # Failed validation
    
    # Factor 2: Errors
    if has_errors:
        confidence -= 0.2
    
    # Factor 3: Warnings
    if has_warnings:
        confidence -= 0.05
    
    # Factor 4: Attempts (penalize retries)
    if attempts > 1:
        penalty = min(0.15, (attempts - 1) * 0.05)
        confidence -= penalty
    
    # Factor 5: Complexity (harder = lower confidence)
    complexity_factors = {
        'EASY': 0.1,
        'MEDIUM': 0.0,
        'HARD': -0.1
    }
    confidence += complexity_factors.get(complexity, 0.0)
    
    # Ensure confidence is in valid range
    confidence = max(0.0, min(1.0, confidence))
    
    return confidence


def generate_explanation(
    command: str,
    is_valid: bool,
    score: float,
    errors: List[str],
    warnings: List[str],
    complexity: str,
    attempts: int,
    corrected: bool
) -> str:
    """
    Generate human-readable explanation of the decision
    
    Args:
        command: Generated command
        is_valid: Validation result
        score: Validation score
        errors: List of errors
        warnings: List of warnings
        complexity: Command complexity
        attempts: Number of attempts
        corrected: Whether command was corrected
        
    Returns:
        Explanation string
    """
    parts = []
    
    # Main status
    if is_valid:
        parts.append(f"✅ Valid {complexity} complexity command generated")
    else:
        parts.append(f"⚠️ Generated command has validation issues")
    
    # Correction status
    if corrected and attempts > 1:
        parts.append(f"Command was corrected after {attempts} attempts")
    elif attempts > 1:
        parts.append(f"Generated in {attempts} attempts")
    
    # Errors
    if errors:
        parts.append(f"Errors found: {', '.join(errors[:2])}")
        if len(errors) > 2:
            parts.append(f"... and {len(errors) - 2} more")
    
    # Warnings
    if warnings:
        parts.append(f"Warnings: {', '.join(warnings[:2])}")
        if len(warnings) > 2:
            parts.append(f"... and {len(warnings) - 2} more")
    
    # Score interpretation
    if score >= 0.9:
        parts.append("High confidence in command validity")
    elif score >= 0.7:
        parts.append("Moderate confidence in command validity")
    elif score >= 0.5:
        parts.append("Low confidence - review recommended")
    else:
        parts.append("Very low confidence - manual review required")
    
    return ". ".join(parts) + "."


def get_recommendation(confidence: float) -> str:
    """
    Get recommendation based on confidence score
    
    Args:
        confidence: Confidence score (0-1)
        
    Returns:
        Recommendation string
    """
    if confidence >= 0.85:
        return "Command appears safe to execute"
    elif confidence >= 0.7:
        return "Review command before executing"
    elif confidence >= 0.5:
        return "Carefully review - consider modifying"
    else:
        return "Do not execute - regenerate or create manually"


# Test
if __name__ == "__main__":
    print("=" * 60)
    print("DECISION AGENT TESTS")
    print("=" * 60)
    
    # Test case 1: Perfect command
    print("\nTest 1: High quality command")
    print("-" * 60)
    
    validation1 = {
        "valid": True,
        "score": 0.95,
        "errors": [],
        "warnings": [],
        "feedback": "Valid command"
    }
    
    gen_info1 = {
        "complexity": "MEDIUM",
        "attempts": 1,
        "corrected": False
    }
    
    decision1 = make_decision(
        "nmap -sV -p 80,443 192.168.1.0/24",
        validation1,
        gen_info1
    )
    
    print(f"Command: {decision1['command']}")
    print(f"Confidence: {decision1['confidence']:.2f}")
    print(f"Explanation: {decision1['explanation']}")
    print(f"Recommendation: {get_recommendation(decision1['confidence'])}")
    
    # Test case 2: Corrected command with warnings
    print("\nTest 2: Corrected command with warnings")
    print("-" * 60)
    
    validation2 = {
        "valid": True,
        "score": 0.75,
        "errors": [],
        "warnings": ["Aggressive timing may be detected"],
        "feedback": "Valid with warnings"
    }
    
    gen_info2 = {
        "complexity": "HARD",
        "attempts": 3,
        "corrected": True
    }
    
    decision2 = make_decision(
        "nmap -sS -T4 --script vuln 192.168.1.1",
        validation2,
        gen_info2
    )
    
    print(f"Command: {decision2['command']}")
    print(f"Confidence: {decision2['confidence']:.2f}")
    print(f"Explanation: {decision2['explanation']}")
    print(f"Recommendation: {get_recommendation(decision2['confidence'])}")
    
    # Test case 3: Invalid command
    print("\nTest 3: Invalid command")
    print("-" * 60)
    
    validation3 = {
        "valid": False,
        "score": 0.3,
        "errors": ["Syntax: Invalid flag", "Safety: Dangerous pattern"],
        "warnings": [],
        "feedback": "Invalid"
    }
    
    gen_info3 = {
        "complexity": "EASY",
        "attempts": 3,
        "corrected": True
    }
    
    decision3 = make_decision(
        "nmap --invalid-flag > output.txt 192.168.1.1",
        validation3,
        gen_info3
    )
    
    print(f"Command: {decision3['command']}")
    print(f"Confidence: {decision3['confidence']:.2f}")
    print(f"Explanation: {decision3['explanation']}")
    print(f"Recommendation: {get_recommendation(decision3['confidence'])}")
    
    print("\n" + "=" * 60)
    print("DECISION AGENT TESTS COMPLETE")
    print("=" * 60)
