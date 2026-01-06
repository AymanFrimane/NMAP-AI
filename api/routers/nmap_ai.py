"""
NMAP-AI Router - Person 4
REST endpoints for validation and command generation

Endpoints:
- POST /api/validate - Validate an nmap command
- POST /api/generate - Generate nmap command from natural language
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import traceback

# Import Person 4's validator
try:
    from agents.validator.validator import CommandValidator
    VALIDATOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Could not import CommandValidator: {e}")
    VALIDATOR_AVAILABLE = False

# Create router
router = APIRouter()

# Initialize validator (will be None if import failed)
validator = None
if VALIDATOR_AVAILABLE:
    try:
        validator = CommandValidator(kg_client=None)
        print("✅ CommandValidator initialized successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize CommandValidator: {e}")

# ============================================================================
# Request/Response Models
# ============================================================================

class ValidateRequest(BaseModel):
    """
    Request to validate an nmap command
    """
    command: str = Field(
        ...,
        description="Nmap command to validate",
        example="nmap -sV -p 80,443 192.168.1.1"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "command": "nmap -sV -p 80,443 192.168.1.1"
            }
        }


class ValidateResponse(BaseModel):
    """
    Validation result
    """
    valid: bool = Field(..., description="Whether the command is valid")
    is_valid: bool = Field(..., description="Whether the command is valid (alias)")
    score: float = Field(..., description="Validation score (0.0 to 1.0)")
    feedback: str = Field(..., description="Human-readable feedback")
    errors: List[str] = Field(default_factory=list, description="List of errors")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional validation details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "is_valid": True,
                "score": 0.95,
                "feedback": "Command is valid and safe to execute",
                "errors": [],
                "warnings": ["This scan requires root privileges"],
                "details": {
                    "syntax": "valid",
                    "conflicts": "none",
                    "safety": "safe"
                }
            }
        }


class GenerateRequest(BaseModel):
    """
    Request to generate an nmap command
    """
    query: str = Field(
        ...,
        description="Natural language description of what to scan",
        example="Scan web servers with version detection on 192.168.1.0/24"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Scan web servers with version detection on 192.168.1.0/24"
            }
        }


class GenerateResponse(BaseModel):
    """
    Generated command with validation
    """
    command: str = Field(..., description="Generated nmap command")
    confidence: float = Field(..., description="Confidence score (0.0 to 1.0)")
    explanation: str = Field(..., description="Explanation of the command")
    validation: ValidateResponse = Field(..., description="Validation result")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "command": "nmap -sV -p 80,443 192.168.1.0/24",
                "confidence": 0.92,
                "explanation": "This command scans the network for web servers and detects their versions",
                "validation": {
                    "valid": True,
                    "is_valid": True,
                    "score": 0.95,
                    "feedback": "Command is valid",
                    "errors": [],
                    "warnings": []
                },
                "metadata": {
                    "complexity": "MEDIUM",
                    "attempts": 1
                }
            }
        }


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/validate", response_model=ValidateResponse)
async def validate_command(request: ValidateRequest) -> ValidateResponse:
    """
    Validate an nmap command
    
    Person 4's main endpoint - validates syntax, conflicts, and safety
    
    Args:
        request: ValidateRequest with command to validate
        
    Returns:
        ValidateResponse with validation results
        
    Raises:
        HTTPException: If validation service is unavailable or fails
    """
    # Check if validator is available
    if not VALIDATOR_AVAILABLE or validator is None:
        raise HTTPException(
            status_code=503,
            detail="Validation service unavailable - CommandValidator not initialized"
        )
    
    try:
        # Validate the command
        result = validator.full_validation(request.command)
        
        # Ensure both 'valid' and 'is_valid' are set
        is_valid = result.get('is_valid', result.get('valid', False))
        
        return ValidateResponse(
            valid=is_valid,
            is_valid=is_valid,
            score=result.get('score', 0.0),
            feedback=result.get('feedback', 'Validation completed'),
            errors=result.get('errors', []),
            warnings=result.get('warnings', []),
            details=result.get('details', {})
        )
        
    except Exception as e:
        # Log the error
        print(f"❌ Validation error: {e}")
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@router.post("/generate", response_model=GenerateResponse)
async def generate_command(request: GenerateRequest) -> GenerateResponse:
    """
    Generate nmap command from natural language
    
    This is a STUB for Day 1 - returns a simple command
    Full implementation requires P1 (comprehension) and P2/P3 (generation)
    
    Args:
        request: GenerateRequest with natural language query
        
    Returns:
        GenerateResponse with generated command and validation
    """
    # STUB IMPLEMENTATION - Day 1
    # TODO: Integrate with P1 (comprehension) and P2/P3 (generators)
    
    # For now, return a simple command based on keywords
    query_lower = request.query.lower()
    
    # Simple keyword-based generation (STUB)
    if 'ping' in query_lower or 'check' in query_lower and 'up' in query_lower:
        command = "nmap -sn 192.168.1.0/24"
        explanation = "Ping scan to check which hosts are up"
    elif 'web' in query_lower or 'http' in query_lower:
        command = "nmap -sV -p 80,443 192.168.1.0/24"
        explanation = "Scan for web servers with version detection"
    elif 'ssh' in query_lower:
        command = "nmap -sV -p 22 192.168.1.0/24"
        explanation = "Scan for SSH servers with version detection"
    elif 'all' in query_lower and 'port' in query_lower:
        command = "nmap -p- 192.168.1.1"
        explanation = "Scan all 65535 ports"
    else:
        # Default command
        command = "nmap -sV 192.168.1.1"
        explanation = "Basic scan with version detection (default for unrecognized query)"
    
    # Validate the generated command
    if VALIDATOR_AVAILABLE and validator is not None:
        try:
            validation_result = validator.full_validation(command)
            is_valid = validation_result.get('is_valid', validation_result.get('valid', False))
            
            validation = ValidateResponse(
                valid=is_valid,
                is_valid=is_valid,
                score=validation_result.get('score', 0.0),
                feedback=validation_result.get('feedback', ''),
                errors=validation_result.get('errors', []),
                warnings=validation_result.get('warnings', []),
                details=validation_result.get('details', {})
            )
            
            # Calculate confidence based on validation
            confidence = validation_result.get('score', 0.5)
            
        except Exception as e:
            print(f"⚠️  Validation failed during generation: {e}")
            # Return with low confidence if validation fails
            validation = ValidateResponse(
                valid=False,
                is_valid=False,
                score=0.0,
                feedback="Could not validate generated command",
                errors=[str(e)],
                warnings=[]
            )
            confidence = 0.3
    else:
        # If validator not available, return unvalidated
        validation = ValidateResponse(
            valid=True,
            is_valid=True,
            score=0.5,
            feedback="Validation service unavailable - command not validated",
            errors=[],
            warnings=["Validation service unavailable"]
        )
        confidence = 0.5
    
    return GenerateResponse(
        command=command,
        confidence=confidence,
        explanation=f"{explanation}\n\n⚠️  Note: This is a STUB implementation (Day 1). "
                   f"Full NL→Command generation requires P1 (comprehension) and P2/P3 (generators).",
        validation=validation,
        metadata={
            "complexity": "MEDIUM",
            "attempts": 1,
            "corrected": False,
            "stub": True
        }
    )


@router.get("/status")
async def get_status():
    """
    Get status of validation and generation services
    
    Returns:
        Service status information
    """
    return {
        "validator": {
            "available": VALIDATOR_AVAILABLE and validator is not None,
            "status": "online" if (VALIDATOR_AVAILABLE and validator is not None) else "offline",
            "message": "Validator ready" if (VALIDATOR_AVAILABLE and validator is not None) else "Validator not initialized"
        },
        "generator": {
            "available": False,
            "status": "stub",
            "message": "Using stub implementation - requires P1/P2/P3 integration"
        },
        "endpoints": {
            "/api/validate": "Validate nmap commands (Person 4)",
            "/api/generate": "Generate nmap commands (STUB - Day 1)",
            "/api/status": "Service status"
        }
    }


# ============================================================================
# Additional Helper Endpoints
# ============================================================================

@router.post("/validate/quick")
async def quick_validate(request: ValidateRequest):
    """
    Quick validation - just returns True/False
    
    Faster endpoint for simple validation checks
    """
    if not VALIDATOR_AVAILABLE or validator is None:
        raise HTTPException(
            status_code=503,
            detail="Validation service unavailable"
        )
    
    try:
        is_valid = validator.quick_validation(request.command)
        return {"valid": is_valid}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Quick validation failed: {str(e)}"
        )


# ============================================================================
# Initialization Check
# ============================================================================

if not VALIDATOR_AVAILABLE:
    print("⚠️  WARNING: CommandValidator not available!")
    print("   Make sure agents/validator modules are properly installed")
    print("   /api/validate endpoint will return 503 errors")
else:
    print("✅ NMAP-AI router initialized with Person 4's validator")