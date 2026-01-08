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
import httpx
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# HARD Model Service Configuration
# ============================================================================
HARD_MODEL_SERVICE_URL = "http://localhost:8001"
_http_client: Optional[httpx.AsyncClient] = None

# Import Person 4's validator
try:
    from agents.validator.validator import CommandValidator
    VALIDATOR_AVAILABLE = True
except ImportError as e:
    print(f"âš ï¸  Warning: Could not import CommandValidator: {e}")
    VALIDATOR_AVAILABLE = False

# Create router
router = APIRouter()

# Initialize validator (will be None if import failed)
validator = None
if VALIDATOR_AVAILABLE:
    try:
        validator = CommandValidator(kg_client=None)
        print("OK CommandValidator initialized successfully")
    except Exception as e:
        print(f"âš ï¸  Warning: Could not initialize CommandValidator: {e}")


# ============================================================================
# Helper Functions for HARD Service Communication
# ============================================================================

async def get_http_client() -> httpx.AsyncClient:
    """Get or create HTTP client for HARD service communication"""
    global _http_client
    
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            base_url=HARD_MODEL_SERVICE_URL,
            timeout=httpx.Timeout(300.0, connect=10.0),  # 5 min for generation, 10s for connect
            follow_redirects=True
        )
    
    return _http_client


async def check_hard_service_health() -> Dict[str, Any]:
    """Check if HARD model service is healthy"""
    try:
        client = await get_http_client()
        response = await client.get("/health", timeout=5.0)
        response.raise_for_status()
        return response.json()
    except httpx.RequestError:
        return {
            "status": "offline",
            "model_loaded": False,
            "message": "Service not reachable"
        }
    except httpx.HTTPStatusError as e:
        return {
            "status": "error",
            "model_loaded": False,
            "message": f"Service error: {e.response.status_code}"
        }
    except Exception as e:
        return {
            "status": "error",
            "model_loaded": False,
            "message": str(e)
        }

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



class HardGenerateRequest(BaseModel):
    """Request for HARD generator"""
    query: str = Field(
        ...,
        description="Natural language description for complex scan",
        example="UDP SNMP brute force on 10.0.0.1"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "UDP SNMP brute force on 10.0.0.1"
            }
        }


class HardGenerateResponse(BaseModel):
    """Response from HARD generator"""
    query: str = Field(..., description="Original query")
    command: str = Field(..., description="Generated complex nmap command")
    complexity: str = Field(default="HARD", description="Complexity level")
    confidence: float = Field(default=0.85, description="Confidence score")
    generation_time: Optional[float] = Field(None, description="Time taken to generate (seconds)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "UDP SNMP brute force on 10.0.0.1",
                "command": "sudo nmap -sU --script snmp-brute -p 161 10.0.0.1",
                "complexity": "HARD",
                "confidence": 0.85,
                "generation_time": 45.2
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
        print(f"âŒ Validation error: {e}")
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
            print(f"âš ï¸  Validation failed during generation: {e}")
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
        explanation=f"{explanation}\n\nâš ï¸  Note: This is a STUB implementation (Day 1). "
                   f"Full NLâ†’Command generation requires P1 (comprehension) and P2/P3 (generators).",
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
        Service status information including HARD generator service
    """
    # Check HARD service health
    hard_health = await check_hard_service_health()
    
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
        "easy_generator": {
            "available": True,
            "status": "online",
            "message": "EASY commands (simple scans, single flags)"
        },
        "medium_generator": {
            "available": True,
            "status": "online",
            "message": "MEDIUM commands (moderate complexity, up to 3 flags)"
        },
        "hard_generator": {
            "available": hard_health.get("status") == "healthy",
            "status": hard_health.get("status", "unknown"),
            "service_url": HARD_MODEL_SERVICE_URL,
            "model_loaded": hard_health.get("model_loaded", False),
            "message": hard_health.get("message", "Check /hard/health for details")
        },
        "endpoints": {
            "/api/validate": "Validate nmap commands (Person 4)",
            "/api/validate/quick": "Quick validation (True/False only)",
            "/api/generate": "Generate nmap commands (STUB - Day 1)",
            "/api/generate/easy": "Generate EASY commands (simple scans)",
            "/api/generate/medium": "Generate MEDIUM commands (moderate complexity)",
            "/api/generate/hard": "Generate HARD commands (complex - Separate Service)",
            "/api/hard/health": "HARD generator health check",
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
# HARD GENERATOR ENDPOINTS (Separate Service)

# ============================================================================
# EASY & MEDIUM GENERATOR ENDPOINTS
# ============================================================================

class EasyMediumGenerateRequest(BaseModel):
    """Request for EASY/MEDIUM generator"""
    query: str = Field(
        ...,
        description="Natural language description",
        example="Scan for web servers on 192.168.1.0/24"
    )
    complexity: str = Field(
        default="MEDIUM",
        description="Complexity level: EASY or MEDIUM",
        pattern="^(EASY|MEDIUM)$"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Scan for SSH on 10.0.0.1",
                "complexity": "EASY"
            }
        }


class EasyMediumGenerateResponse(BaseModel):
    """Response from EASY/MEDIUM generator"""
    query: str = Field(..., description="Original query")
    command: str = Field(..., description="Generated nmap command")
    complexity: str = Field(..., description="Complexity level used")
    confidence: float = Field(..., description="Confidence score")
    generation_time: Optional[float] = Field(None, description="Time taken to generate (seconds)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Scan for SSH on 10.0.0.1",
                "command": "nmap -sV -p 22 10.0.0.1",
                "complexity": "EASY",
                "confidence": 0.90,
                "generation_time": 1.2
            }
        }


@router.post("/generate/easy", response_model=EasyMediumGenerateResponse)
async def generate_easy_command(request: EasyMediumGenerateRequest):
    """
    Generate EASY nmap command
    
    EASY commands are simple, single-purpose scans:
    - Single flag operations
    - No port specifications or simple port ranges
    - Basic scan types (ping, TCP connect, version detection)
    
    Args:
        request: Query with optional complexity override
        
    Returns:
        EasyMediumGenerateResponse with generated command
    """
    request.complexity = "EASY"  # Force EASY level
    return await _generate_easy_medium_command(request)


@router.post("/generate/medium", response_model=EasyMediumGenerateResponse)
async def generate_medium_command(request: EasyMediumGenerateRequest):
    """
    Generate MEDIUM nmap command
    
    MEDIUM commands are moderate complexity:
    - Up to 3 flags
    - May include port specifications (-p)
    - Service/version detection (-sV)
    - OS detection (-O)
    - Common scan combinations
    
    Args:
        request: Query with optional complexity override
        
    Returns:
        EasyMediumGenerateResponse with generated command
    """
    request.complexity = "MEDIUM"  # Force MEDIUM level
    return await _generate_easy_medium_command(request)


async def _generate_easy_medium_command(request: EasyMediumGenerateRequest) -> EasyMediumGenerateResponse:
    """
    Internal function to generate EASY/MEDIUM commands
    
    Strategy:
    1. Try P2 generator if available (direct import)
    2. Fall back to enhanced stub generation
    3. Always validate the result
    """
    try:
        start_time = time.time()
        logger.info(f"[{request.complexity}] Generating command for: {request.query}")
        
        # Try P2 generator first (if available from commented code)
        # For now, use enhanced stub generation
        command = _enhanced_stub_generate(request.query, request.complexity)
        
        # Validate the generated command
        if VALIDATOR_AVAILABLE and validator is not None:
            try:
                validation_result = validator.full_validation(command)
                confidence = validation_result.get('score', 0.75)
            except Exception as e:
                logger.warning(f"Validation failed: {e}")
                confidence = 0.6
        else:
            confidence = 0.7
        
        generation_time = time.time() - start_time
        logger.info(f"OK Generated in {generation_time:.2f}s: {command}")
        
        return EasyMediumGenerateResponse(
            query=request.query,
            command=command,
            complexity=request.complexity,
            confidence=confidence,
            generation_time=generation_time
        )
        
    except Exception as e:
        logger.error(f"ERR {request.complexity} generation failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"{request.complexity} generation failed: {str(e)}"
        )


def _enhanced_stub_generate(query: str, complexity: str) -> str:
    """
    Enhanced stub generation for EASY/MEDIUM commands
    
    This is a fallback when P2 generator is not available.
    Provides better command generation than simple keyword matching.
    """
    query_lower = query.lower()
    
    # Extract target if present
    import re
    target_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b', query)
    target = target_match.group(0) if target_match else "192.168.1.1"
    
    if complexity == "EASY":
        # EASY: Single purpose, simple commands
        if 'ping' in query_lower or ('check' in query_lower and 'up' in query_lower):
            return f"nmap -sn {target}"
        elif 'ssh' in query_lower:
            return f"nmap -p 22 {target}"
        elif 'web' in query_lower or 'http' in query_lower:
            return f"nmap -p 80,443 {target}"
        elif 'ftp' in query_lower:
            return f"nmap -p 21 {target}"
        elif 'dns' in query_lower:
            return f"nmap -p 53 {target}"
        elif 'smtp' in query_lower or 'mail' in query_lower:
            return f"nmap -p 25 {target}"
        else:
            # Default simple scan
            return f"nmap {target}"
    
    else:  # MEDIUM
        # MEDIUM: Multiple flags, port ranges, version detection
        ports = []
        flags = []
        
        # Detect services and build port list
        if 'web' in query_lower or 'http' in query_lower:
            ports.extend(['80', '443', '8080'])
        if 'ssh' in query_lower:
            ports.append('22')
        if 'ftp' in query_lower:
            ports.append('21')
        if 'dns' in query_lower:
            ports.append('53')
        if 'smtp' in query_lower or 'mail' in query_lower:
            ports.extend(['25', '587'])
        if 'database' in query_lower or 'db' in query_lower:
            ports.extend(['3306', '5432', '1433'])
        
        # Detect scan type
        if 'version' in query_lower or 'detect' in query_lower:
            flags.append('-sV')
        if 'os' in query_lower or 'operating system' in query_lower:
            flags.append('-O')
        if 'all port' in query_lower:
            ports = ['-']  # All ports
        
        # Build command
        cmd_parts = ['nmap']
        
        # Add flags
        if flags:
            cmd_parts.extend(flags)
        elif not ports:
            # If no specific flags/ports, add version detection
            cmd_parts.append('-sV')
        
        # Add ports
        if ports:
            if '-' in ports:
                cmd_parts.extend(['-p-'])
            elif ports:
                cmd_parts.extend(['-p', ','.join(ports)])
        
        # Add target
        cmd_parts.append(target)
        
        return ' '.join(cmd_parts)

# ============================================================================

@router.get("/hard/health")
async def hard_health_check():
    """
    Check HARD generator status (from separate standalone application)
    
    The HARD model runs as a separate service on port 8001 to avoid
    memory/resource conflicts with the main API.
    
    Returns:
        Health status of the HARD model service
    """
    health = await check_hard_service_health()
    
    return {
        "status": health.get("status", "unknown"),
        "hard_generator_loaded": health.get("model_loaded", False),
        "message": health.get("message", "Unknown status"),
        "service_url": HARD_MODEL_SERVICE_URL,
        "note": "Hard model runs as a separate standalone application on port 8001"
    }


@router.post("/generate/hard", response_model=HardGenerateResponse)
async def generate_hard_command(request: HardGenerateRequest):
    """
    Generate complex HARD nmap command
    
    Delegates to separate standalone hard model application (port 8001).
    First request triggers model loading (30-60s).
    Subsequent requests take 20-90s on CPU.
    
    **NOTE**: Hard model service must be running separately!
    Start it with: `python hard_model_service.py`
    
    Args:
        request: HardGenerateRequest with query
        
    Returns:
        HardGenerateResponse with generated command
        
    Raises:
        HTTPException: If service is unavailable or generation fails
    """
    try:
        logger.info(f"[HARD]  Requesting HARD command generation for: {request.query}")
        start_time = time.time()
        
        # Call separate standalone hard model service
        client = await get_http_client()
        response = await client.post(
            "/generate",
            json={"query": request.query}
        )
        response.raise_for_status()
        
        result = response.json()
        elapsed = time.time() - start_time
        
        logger.info(f"OK Generated in {elapsed:.1f}s: {result.get('command', 'N/A')}")
        
        return HardGenerateResponse(
            query=result.get("query", request.query),
            command=result.get("command", ""),
            complexity=result.get("complexity", "HARD"),
            confidence=result.get("confidence", 0.85),
            generation_time=result.get("generation_time", elapsed)
        )
        
    except httpx.RequestError as e:
        logger.error(f"ERR Hard model service unreachable: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Hard model service at {HARD_MODEL_SERVICE_URL} is not running. "
                   f"Please start it separately with: python hard_model_service.py"
        )
        
    except httpx.HTTPStatusError as e:
        logger.error(f"ERR Hard model service error: {e}")
        error_detail = "Unknown error"
        try:
            error_detail = e.response.json().get("detail", str(e))
        except:
            error_detail = str(e)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Hard model service error: {error_detail}"
        )
        
    except Exception as e:
        logger.error(f"ERR Generation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)}"
        )


# ============================================================================
# Initialization Check
# ============================================================================

if not VALIDATOR_AVAILABLE:
    print("âš ï¸  WARNING: CommandValidator not available!")
    print("   Make sure agents/validator modules are properly installed")
    print("   /api/validate endpoint will return 503 errors")
else:
    print("OK NMAP-AI router initialized with Person 4's validator")
print("\n[HARD] HARD Generator Configuration:")
print(f"   Service URL: {HARD_MODEL_SERVICE_URL}")
print("   Status: Check /hard/health endpoint")
print("   Note: HARD model runs as a separate service")
print("   Start with: python hard_model_service.py")















































# """
# NMAP-AI Router - Person 4
# REST endpoints for validation and command generation

# INTEGRATED WITH P2 (Direct Import):
# - Imports T5NmapGenerator directly from agents.easy_medium
# - Validates with P4's validator
# - Applies self-correction
# - Returns final decision with confidence

# Endpoints:
# - POST /api/validate - Validate an nmap command
# - POST /api/generate - Generate nmap command from natural language
# """

# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel, Field
# from typing import Optional, List, Dict, Any
# import traceback
# import logging
# import sys
# from pathlib import Path

# # Setup logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Add project root to path
# project_root = Path(__file__).parent.parent.parent
# sys.path.insert(0, str(project_root))

# # Import P4's modules
# try:
#     from agents.validator.validator import CommandValidator
#     from agents.validator.self_correct import SelfCorrector
#     from agents.validator.decision import make_decision
#     VALIDATOR_AVAILABLE = True
#     logger.info("✅ P4 validator modules loaded")
# except ImportError as e:
#     logger.error(f"❌ Could not import P4 validator: {e}")
#     VALIDATOR_AVAILABLE = False

# # Import P1's comprehension
# try:
#     from agents.comprehension.classifier import get_classifier
#     from agents.comprehension.kg_utils import get_kg_client
#     P1_AVAILABLE = True
#     logger.info("✅ P1 comprehension modules loaded")
# except ImportError as e:
#     logger.warning(f"⚠️ P1 not available: {e}")
#     P1_AVAILABLE = False

# # 🔥 Import P2 directly (no API needed!)
# try:
#     from agents.easy_medium.t5_generator import T5NmapGenerator
#     P2_AVAILABLE = True
#     logger.info("✅ P2 T5NmapGenerator loaded")
# except ImportError as e:
#     logger.warning(f"⚠️ P2 not available: {e}")
#     P2_AVAILABLE = False

# # Create router
# router = APIRouter()

# # Initialize components
# validator = None
# kg_client = None
# p2_generator = None

# # Initialize validator
# if VALIDATOR_AVAILABLE:
#     try:
#         if P1_AVAILABLE:
#             kg_client = get_kg_client()
#             logger.info("✅ KG client initialized")
        
#         validator = CommandValidator(kg_client=kg_client)
#         logger.info("✅ CommandValidator initialized")
#     except Exception as e:
#         logger.error(f"❌ Could not initialize validator: {e}")

# # 🔥 Initialize P2 generator directly
# if P2_AVAILABLE:
#     try:
#         # Path to P2's model
#         model_path = project_root / "agents" / "easy_medium" / "models" / "nmap_adapter_premium"
        
#         if model_path.exists():
#             p2_generator = T5NmapGenerator(str(model_path))
#             logger.info("✅ P2 generator initialized with model")
#         else:
#             logger.warning(f"⚠️ P2 model not found at {model_path}")
#             p2_generator = None
#     except Exception as e:
#         logger.error(f"❌ Could not initialize P2 generator: {e}")
#         p2_generator = None


# # ============================================================================
# # Request/Response Models
# # ============================================================================

# class ValidateRequest(BaseModel):
#     """Request to validate an nmap command"""
#     command: str = Field(
#         ...,
#         description="Nmap command to validate",
#         example="nmap -sV -p 80,443 192.168.1.1"
#     )


# class ValidateResponse(BaseModel):
#     """Validation result"""
#     valid: bool
#     is_valid: bool
#     score: float
#     feedback: str
#     errors: List[str] = []
#     warnings: List[str] = []
#     details: Optional[Dict[str, Any]] = None


# class GenerateRequest(BaseModel):
#     """Request to generate an nmap command"""
#     query: str = Field(
#         ...,
#         description="Natural language description",
#         example="Scan web servers with version detection on 192.168.1.0/24"
#     )
#     use_self_correction: bool = Field(
#         True,
#         description="Apply self-correction if validation fails"
#     )
#     max_retries: int = Field(
#         3,
#         description="Maximum self-correction attempts"
#     )


# class GenerateResponse(BaseModel):
#     """Generated command with validation"""
#     command: str
#     confidence: float
#     explanation: str
#     validation: ValidateResponse
#     metadata: Dict[str, Any]


# # ============================================================================
# # Endpoints
# # ============================================================================

# @router.post("/validate", response_model=ValidateResponse)
# async def validate_command(request: ValidateRequest) -> ValidateResponse:
#     """
#     Validate an nmap command
    
#     Person 4's main endpoint - validates syntax, conflicts, and safety
#     """
#     if not VALIDATOR_AVAILABLE or validator is None:
#         raise HTTPException(
#             status_code=503,
#             detail="Validation service unavailable"
#         )
    
#     try:
#         result = validator.full_validation(request.command)
        
#         is_valid = result.get('is_valid', result.get('valid', False))
        
#         return ValidateResponse(
#             valid=is_valid,
#             is_valid=is_valid,
#             score=result.get('score', 0.0),
#             feedback=result.get('feedback', 'Validation completed'),
#             errors=result.get('errors', []),
#             warnings=result.get('warnings', []),
#             details=result.get('details', {})
#         )
        
#     except Exception as e:
#         logger.error(f"❌ Validation error: {e}")
#         traceback.print_exc()
        
#         raise HTTPException(
#             status_code=500,
#             detail=f"Validation failed: {str(e)}"
#         )


# @router.post("/generate", response_model=GenerateResponse)
# async def generate_command(request: GenerateRequest) -> GenerateResponse:
#     """
#     Generate nmap command from natural language
    
#     FULLY INTEGRATED PIPELINE (Direct Import):
#     1. P1: Get complexity from query
#     2. P2: Generate command (direct call to T5NmapGenerator)
#     3. P4: Validate command
#     4. P4: Apply self-correction if needed
#     5. P4: Return final decision with confidence
#     """
    
#     # ========================================================================
#     # STEP 1: Detect Complexity (P1)
#     # ========================================================================
    
#     complexity = "MEDIUM"  # Default
    
#     if P1_AVAILABLE:
#         try:
#             classifier = get_classifier()
#             result = classifier.comprehend(request.query)
            
#             if result.get('is_relevant'):
#                 complexity = result.get('complexity', 'MEDIUM')
#                 logger.info(f"✅ P1 detected complexity: {complexity}")
#             else:
#                 raise HTTPException(
#                     status_code=400,
#                     detail="Query is not relevant to nmap scanning"
#                 )
#         except Exception as e:
#             logger.warning(f"⚠️ P1 comprehension failed: {e}, using default")
#     else:
#         logger.info("⚠️ P1 not available, using default complexity")
    
#     # ========================================================================
#     # STEP 2: Generate Command (P2 Direct Call)
#     # ========================================================================
    
#     if P2_AVAILABLE and p2_generator:
#         try:
#             # 🔥 Call P2 generator directly (no HTTP!)
#             command = p2_generator.generate(request.query, complexity)
            
#             if not command or not command.startswith("nmap"):
#                 raise ValueError("Invalid command generated")
            
#             logger.info(f"✅ P2 generated command: {command}")
            
#         except Exception as e:
#             logger.error(f"❌ P2 generation error: {e}")
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Command generation failed: {str(e)}"
#             )
#     else:
#         # Fallback: simple stub generation
#         logger.warning("⚠️ P2 not available, using stub generation")
#         command = _stub_generate(request.query, complexity)
    
#     # ========================================================================
#     # STEP 3: Validate Command (P4)
#     # ========================================================================
    
#     if not VALIDATOR_AVAILABLE or validator is None:
#         raise HTTPException(
#             status_code=503,
#             detail="Validation service unavailable"
#         )
    
#     validation_result = validator.full_validation(command)
#     is_valid = validation_result.get('is_valid', False)
    
#     logger.info(f"✅ Validation: valid={is_valid}, score={validation_result.get('score')}")
    
#     # ========================================================================
#     # STEP 4: Self-Correction (P4) - If needed
#     # ========================================================================
    
#     attempts = 1
#     corrected = False
    
#     if request.use_self_correction and not is_valid and P2_AVAILABLE and p2_generator:
#         logger.info("🔄 Starting self-correction loop...")
        
#         corrector = SelfCorrector(max_retries=request.max_retries)
        
#         # Generator function that calls P2 directly
#         def generator_func(intent: str, comp: str) -> str:
#             return p2_generator.generate(intent, comp)
        
#         # Self-correction loop
#         correction_result = corrector.loop(
#             intent=request.query,
#             complexity=complexity,
#             generator_func=generator_func,
#             validator_func=validator.full_validation
#         )
        
#         command = correction_result['command']
#         validation_result = correction_result['validation']
#         attempts = correction_result['attempts']
#         corrected = correction_result['corrected']
        
#         logger.info(f"✅ Self-correction: attempts={attempts}, corrected={corrected}")
    
#     # ========================================================================
#     # STEP 5: Final Decision (P4)
#     # ========================================================================
    
#     decision = make_decision(
#         command=command,
#         validation=validation_result,
#         generation_info={
#             'complexity': complexity,
#             'attempts': attempts,
#             'corrected': corrected
#         }
#     )
    
#     logger.info(f"✅ Final decision: confidence={decision['confidence']:.2f}")
    
#     # ========================================================================
#     # Build Response
#     # ========================================================================
    
#     is_valid_final = validation_result.get('is_valid', validation_result.get('valid', False))
    
#     validation_response = ValidateResponse(
#         valid=is_valid_final,
#         is_valid=is_valid_final,
#         score=validation_result.get('score', 0.0),
#         feedback=validation_result.get('feedback', ''),
#         errors=validation_result.get('errors', []),
#         warnings=validation_result.get('warnings', []),
#         details=validation_result.get('details', {})
#     )
    
#     metadata = {
#         'complexity': complexity,
#         'attempts': attempts,
#         'corrected': corrected,
#         'p1_available': P1_AVAILABLE,
#         'p2_available': P2_AVAILABLE and p2_generator is not None,
#         'p2_mode': 'direct_import',  # 🔥 New: indicate we're using direct import
#         'self_correction_used': request.use_self_correction and corrected
#     }
    
#     return GenerateResponse(
#         command=command,
#         confidence=decision['confidence'],
#         explanation=decision['explanation'],
#         validation=validation_response,
#         metadata=metadata
#     )


# @router.get("/status")
# async def get_status():
#     """Get status of all integrated services"""
    
#     # Check P2 generator status
#     p2_status = "offline"
#     if P2_AVAILABLE and p2_generator is not None:
#         try:
#             # Quick test
#             test_cmd = p2_generator.generate("ping scan localhost", "EASY")
#             if test_cmd and test_cmd.startswith("nmap"):
#                 p2_status = "online"
#         except:
#             p2_status = "error"
    
#     return {
#         "p4_validator": {
#             "available": VALIDATOR_AVAILABLE and validator is not None,
#             "status": "online" if (VALIDATOR_AVAILABLE and validator is not None) else "offline"
#         },
#         "p1_comprehension": {
#             "available": P1_AVAILABLE,
#             "status": "online" if P1_AVAILABLE else "offline"
#         },
#         "p2_generator": {
#             "available": P2_AVAILABLE and p2_generator is not None,
#             "status": p2_status,
#             "mode": "direct_import"  # 🔥 New: show integration mode
#         },
#         "integration": "P1 + P2 (direct) + P4 pipeline",
#         "endpoints": {
#             "/api/validate": "Validate nmap commands (P4)",
#             "/api/generate": "Generate & validate commands (P1+P2+P4 integrated)",
#             "/api/status": "Service status"
#         }
#     }


# @router.post("/validate/quick")
# async def quick_validate(request: ValidateRequest):
#     """Quick validation - just returns True/False"""
#     if not VALIDATOR_AVAILABLE or validator is None:
#         raise HTTPException(
#             status_code=503,
#             detail="Validation service unavailable"
#         )
    
#     try:
#         is_valid = validator.quick_validation(request.command)
#         return {"valid": is_valid}
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Quick validation failed: {str(e)}"
#         )


# # ============================================================================
# # Helper Functions
# # ============================================================================

# def _stub_generate(query: str, complexity: str) -> str:
#     """Fallback stub generation when P2 is not available"""
#     query_lower = query.lower()
    
#     if complexity == "EASY":
#         if 'ping' in query_lower:
#             return "nmap -sn 192.168.1.0/24"
#         else:
#             return "nmap -sV 192.168.1.1"
#     else:  # MEDIUM
#         if 'web' in query_lower or 'http' in query_lower:
#             return "nmap -sV -p 80,443 192.168.1.0/24"
#         elif 'ssh' in query_lower:
#             return "nmap -sV -p 22 192.168.1.0/24"
#         else:
#             return "nmap -sV -p 1-1000 192.168.1.1"



# # ============================================================================
# # Initialization Check
# # ============================================================================

# logger.info("=" * 60)
# logger.info("NMAP-AI Router Initialization (Direct P2 Import)")
# logger.info("=" * 60)
# logger.info(f"P1 (Comprehension): {'✅' if P1_AVAILABLE else '❌'}")
# logger.info(f"P2 (Generator): {'✅ (direct import)' if (P2_AVAILABLE and p2_generator) else '❌'}")
# logger.info(f"P4 (Validator): {'✅' if VALIDATOR_AVAILABLE else '❌'}")
# logger.info("=" * 60)

# if not VALIDATOR_AVAILABLE:
#     logger.error("❌ CRITICAL: P4 validator not available!")
# elif not P2_AVAILABLE or p2_generator is None:
#     logger.warning("⚠️ WARNING: P2 generator not available, using stub generation")
# else:
#     logger.info("✅ Full P1+P2+P4 pipeline ready! (Direct Import Mode)")