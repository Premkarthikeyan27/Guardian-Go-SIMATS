import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "Guardian Go"

def test_landing_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Guardian Go" in response.text

def test_parent_portal_route():
    response = client.get("/portals/user/")
    assert response.status_code == 200
    assert "Parent" in response.text

def test_guardian_portal_route():
    response = client.get("/portals/guardian/")
    assert response.status_code == 200
    assert "Guardian" in response.text

def test_admin_portal_route():
    response = client.get("/portals/admin/")
    assert response.status_code == 200
    assert "Admin" in response.text
