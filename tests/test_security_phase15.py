import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app
from backend.services.security_service import InMemRateLimiter

client = TestClient(app)

def test_security_headers_middleware():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "Content-Security-Policy" in res.headers
    assert "Strict-Transport-Security" in res.headers

def test_security_health_audit_endpoint():
    res = client.get("/api/v1/security/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SECURE"
    assert "security_headers" in data
    assert "rate_limiting" in data
    assert "authentication_security" in data
    assert "data_protection" in data

def test_sensitive_data_masking():
    res = client.post("/api/v1/security/mask-test?aadhaar=998877665544&phone=%2B1%20555-0192&email=sarah.jenkins%40demo.com")
    assert res.status_code == 200
    data = res.json()
    assert data["masked_aadhaar"] == "XXXX-XXXX-5544"
    assert "0192" in data["masked_phone"]
    assert "s***s@demo.com" in data["masked_email"]

def test_in_memory_rate_limiter():
    limiter = InMemRateLimiter(requests_per_minute=3)
    ip = "192.168.1.100"
    assert limiter.is_allowed(ip) is True
    assert limiter.is_allowed(ip) is True
    assert limiter.is_allowed(ip) is True
    # 4th request within minute should be blocked
    assert limiter.is_allowed(ip) is False
