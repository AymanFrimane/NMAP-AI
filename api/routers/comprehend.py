"""
FastAPI Router for Comprehension Agent
Provides /comprehend endpoint for query understanding.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Union

from agents.comprehension import get_classifier


router = APIRouter(prefix="/comprehend", tags=["comprehension"])


class ComprehendRequest(BaseModel):
    """Request model for comprehension."""
    query: str = Field(..., description="Natural language query to comprehend")
    

class ComprehendResponse(BaseModel):
    """Response model for comprehension."""
    intent: str = Field(..., description="Extracted intent from the query")
    is_relevant: bool = Field(..., description="Whether query is nmap-related")
    # FIX: Use Union instead of Optional[Literal] to avoid Pydantic v2 bug
    complexity: Union[str, None] = Field(
        None, 
        description="Complexity level: EASY, MEDIUM, or HARD (null if not relevant)"
    )


@router.post("/", response_model=ComprehendResponse)
async def comprehend_query(request: ComprehendRequest) -> ComprehendResponse:
    """
    Comprehend a natural language query.
    
    Analyzes the query to:
    - Determine if it's relevant to nmap/network scanning
    - Extract the intent
    - Classify complexity level
    
    Args:
        request: Query to analyze
        
    Returns:
        Comprehension result with intent, relevance, and complexity
        
    Raises:
        HTTPException: If classifier is not trained
    """
    try:
        classifier = get_classifier()
        result = classifier.comprehend(request.query)
        
        return ComprehendResponse(**result)
        
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Classifier not ready: {str(e)}. Please train models first."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Comprehension failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Check if the comprehension service is ready.
    
    Returns:
        Status information
    """
    try:
        classifier = get_classifier()
        
        # Try a simple test
        result = classifier.comprehend("test")
        
        return {
            "status": "healthy",
            "service": "comprehension",
            "models_loaded": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "comprehension",
            "models_loaded": False,
            "error": str(e)
        }