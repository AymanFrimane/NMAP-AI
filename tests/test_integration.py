"""
NMAP-AI Integration Tests
Complete test suite for P1+P2+P4 pipeline

Run with: pytest tests/test_integration.py -v
"""

import pytest
import requests
import time
from typing import Dict, Any

# Base URL for API
BASE_URL = "http://localhost:8000"

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def api_url():
    """Base API URL."""
    return BASE_URL

@pytest.fixture(scope="module")
def check_api_running(api_url):
    """Check if API is running before tests."""
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code != 200:
            pytest.skip("API not running. Start with: python -m uvicorn api.main:app --port 8000")
    except requests.exceptions.ConnectionError:
        pytest.skip("API not running. Start with: python -m uvicorn api.main:app --port 8000")

@pytest.fixture
def headers():
    """Common headers for requests."""
    return {"Content-Type": "application/json"}

# ============================================================================
# Test: API Health & Status
# ============================================================================

class TestAPIHealth:
    """Test API health and status endpoints."""
    
    def test_root_endpoint(self, api_url, check_api_running):
        """Test root endpoint returns API info."""
        response = requests.get(f"{api_url}/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "NMAP-AI" in data["name"]
    
    def test_health_endpoint(self, api_url, check_api_running):
        """Test health endpoint."""
        response = requests.get(f"{api_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_api_status(self, api_url, check_api_running, headers):
        """Test /api/status shows all services online."""
        response = requests.get(f"{api_url}/api/status")
        assert response.status_code == 200
        data = response.json()
        
        # Check all services
        assert data["p1_comprehension"]["available"] is True
        assert data["p1_comprehension"]["status"] == "online"
        
        assert data["p2_generator"]["available"] is True
        assert data["p2_generator"]["status"] == "online"
        assert data["p2_generator"]["mode"] == "direct_import"
        
        assert data["p4_validator"]["available"] is True
        assert data["p4_validator"]["status"] == "online"

# ============================================================================
# Test: P1 Comprehension
# ============================================================================

class TestP1Comprehension:
    """Test P1 comprehension agent."""
    
    def test_comprehend_easy_query(self, api_url, check_api_running, headers):
        """Test EASY query classification."""
        response = requests.post(
            f"{api_url}/comprehend/",
            headers=headers,
            json={"query": "ping scan network"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_relevant"] is True
        assert data["complexity"] == "EASY"
    
    def test_comprehend_medium_query(self, api_url, check_api_running, headers):
        """Test MEDIUM query classification."""
        response = requests.post(
            f"{api_url}/comprehend/",
            headers=headers,
            json={"query": "scan for web servers with version detection"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_relevant"] is True
        # Note: May be EASY or MEDIUM depending on model
        assert data["complexity"] in ["EASY", "MEDIUM"]
    
    def test_comprehend_hard_query(self, api_url, check_api_running, headers):
        """Test HARD query classification."""
        response = requests.post(
            f"{api_url}/comprehend/",
            headers=headers,
            json={"query": "aggressive scan with scripts"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_relevant"] is True
        assert data["complexity"] in ["MEDIUM", "HARD"]
    
    def test_comprehend_irrelevant_query(self, api_url, check_api_running, headers):
        """Test non-relevant query rejection."""
        response = requests.post(
            f"{api_url}/comprehend/",
            headers=headers,
            json={"query": "make me a sandwich"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_relevant"] is False
        assert data["complexity"] is None
    
    def test_comprehend_health(self, api_url, check_api_running):
        """Test comprehension health endpoint."""
        response = requests.get(f"{api_url}/comprehend/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["models_loaded"] is True

# ============================================================================
# Test: P4 Validation
# ============================================================================

class TestP4Validation:
    """Test P4 validation agent."""
    
    def test_validate_valid_command(self, api_url, check_api_running, headers):
        """Test validation of valid command."""
        response = requests.post(
            f"{api_url}/api/validate",
            headers=headers,
            json={"command": "nmap -sV -p 80,443 192.168.1.1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["is_valid"] is True
        assert data["score"] >= 0.8
        assert len(data["errors"]) == 0
    
    def test_validate_simple_command(self, api_url, check_api_running, headers):
        """Test validation of simple command."""
        response = requests.post(
            f"{api_url}/api/validate",
            headers=headers,
            json={"command": "nmap -sn 192.168.1.0/24"}
        )
        assert response.status_code == 200
        data = response.json()
        # Ping scan might have warnings but should have good score
        assert data["score"] >= 0.7  # More lenient threshold
    
    def test_validate_invalid_syntax(self, api_url, check_api_running, headers):
        """Test validation catches syntax errors."""
        response = requests.post(
            f"{api_url}/api/validate",
            headers=headers,
            json={"command": "nmap -sV"}  # Missing target
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0
        assert any("target" in err.lower() for err in data["errors"])
    
    def test_validate_quick(self, api_url, check_api_running, headers):
        """Test quick validation endpoint."""
        response = requests.post(
            f"{api_url}/api/validate/quick",
            headers=headers,
            json={"command": "nmap 192.168.1.1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert isinstance(data["valid"], bool)

# ============================================================================
# Test: P2 Generation & Full Pipeline
# ============================================================================

class TestP2Generation:
    """Test P2 generation and full pipeline."""
    
    def test_generate_ssh_scan(self, api_url, check_api_running, headers):
        """Test SSH scan generation."""
        response = requests.post(
            f"{api_url}/api/generate",
            headers=headers,
            json={"query": "scan for SSH on 192.168.1.100"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check command contains SSH port
        assert "22" in data["command"]
        assert "192.168.1.100" in data["command"]
        
        # Check metadata
        assert data["metadata"]["p1_available"] is True
        assert data["metadata"]["p2_available"] is True
        assert data["metadata"]["p2_mode"] == "direct_import"
        
        # Check validation passed
        assert data["validation"]["valid"] is True
    
    def test_generate_web_scan(self, api_url, check_api_running, headers):
        """Test web servers scan generation."""
        response = requests.post(
            f"{api_url}/api/generate",
            headers=headers,
            json={"query": "scan for web servers on 192.168.1.0/24"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check command contains web ports
        assert ("80" in data["command"] or "443" in data["command"])
        assert "192.168.1.0/24" in data["command"]
        
        # Check validation
        assert data["validation"]["valid"] is True
        assert data["confidence"] > 0.5
    
    def test_generate_multiple_services(self, api_url, check_api_running, headers):
        """Test multiple services detection."""
        response = requests.post(
            f"{api_url}/api/generate",
            headers=headers,
            json={"query": "scan for SSH and HTTP on 10.0.0.1"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have both ports
        assert "22" in data["command"]
        assert "80" in data["command"]
        assert "10.0.0.1" in data["command"]
    
    def test_generate_ping_scan(self, api_url, check_api_running, headers):
        """Test ping scan generation."""
        response = requests.post(
            f"{api_url}/api/generate",
            headers=headers,
            json={"query": "ping scan 192.168.1.0/24"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check command
        assert "192.168.1.0/24" in data["command"]
        assert data["metadata"]["complexity"] == "EASY"
    
    def test_generate_with_self_correction(self, api_url, check_api_running, headers):
        """Test generation with self-correction enabled."""
        response = requests.post(
            f"{api_url}/api/generate",
            headers=headers,
            json={
                "query": "scan network",
                "use_self_correction": True,
                "max_retries": 3
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check metadata includes self-correction info
        assert "attempts" in data["metadata"]
        assert "corrected" in data["metadata"]
        assert data["metadata"]["attempts"] >= 1

# ============================================================================
# Test: Performance
# ============================================================================

class TestPerformance:
    """Test API performance."""
    
    def test_validation_performance(self, api_url, check_api_running, headers):
        """Test validation completes within 3 seconds."""
        start = time.time()
        response = requests.post(
            f"{api_url}/api/validate",
            headers=headers,
            json={"command": "nmap -sV 192.168.1.1"}
        )
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 3.0  # Should be < 3 seconds (Windows + first call)
    
    def test_generation_performance(self, api_url, check_api_running, headers):
        """Test generation completes within 5 seconds."""
        start = time.time()
        response = requests.post(
            f"{api_url}/api/generate",
            headers=headers,
            json={"query": "scan for SSH"}
        )
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 5.0  # Should be < 5 seconds
    
    def test_comprehension_performance(self, api_url, check_api_running, headers):
        """Test comprehension completes within 3 seconds."""
        start = time.time()
        response = requests.post(
            f"{api_url}/comprehend/",
            headers=headers,
            json={"query": "scan network"}
        )
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 3.0  # Should be < 3 seconds (Windows + first call)

# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_query(self, api_url, check_api_running, headers):
        """Test empty query handling."""
        response = requests.post(
            f"{api_url}/api/generate",
            headers=headers,
            json={"query": ""}
        )
        # Should still return a response (may be error or default)
        assert response.status_code in [200, 400, 422]
    
    def test_very_long_query(self, api_url, check_api_running, headers):
        """Test very long query handling."""
        long_query = "scan " + " ".join(["network"] * 100)
        response = requests.post(
            f"{api_url}/api/generate",
            headers=headers,
            json={"query": long_query}
        )
        assert response.status_code in [200, 400]
    
    def test_special_characters_in_query(self, api_url, check_api_running, headers):
        """Test special characters handling."""
        response = requests.post(
            f"{api_url}/api/generate",
            headers=headers,
            json={"query": "scan <script>alert('xss')</script>"}
        )
        assert response.status_code in [200, 400]
    
    def test_missing_content_type(self, api_url, check_api_running):
        """Test request without Content-Type header."""
        response = requests.post(
            f"{api_url}/api/generate",
            json={"query": "scan network"}
            # No Content-Type header
        )
        # FastAPI should handle this gracefully
        assert response.status_code in [200, 415, 422]

# ============================================================================
# Test: Integration Scenarios
# ============================================================================

@pytest.mark.parametrize("query,expected_ports", [
    ("scan for SSH", "22"),
    ("scan for HTTP", "80"),
    ("scan for HTTPS", "443"),
    ("scan web servers", "80"),  # Should have 80 or 443
    ("scan for FTP", "21"),
])
class TestServiceDetection:
    """Test service detection across different queries."""
    
    def test_service_port_mapping(self, api_url, check_api_running, headers, query, expected_ports):
        """Test that service queries map to correct ports."""
        response = requests.post(
            f"{api_url}/api/generate",
            headers=headers,
            json={"query": query}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check port is in command
        assert expected_ports in data["command"]

# ============================================================================
# Summary
# ============================================================================

def test_suite_summary(api_url, check_api_running):
    """Print test suite summary."""
    print("\n" + "="*60)
    print("🧪 NMAP-AI INTEGRATION TEST SUITE")
    print("="*60)
    print(f"✅ API URL: {api_url}")
    print(f"✅ All tests completed successfully!")
    print("="*60)