import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

client = TestClient(app)

def test_fetch_admin_command_centre_payload():
    res = client.get("/api/v1/admin/command-centre")
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert "executive_ai_summary" in data
    assert "pending_verifications_list" in data
    assert "open_risk_alerts_list" in data
    assert "open_complaints_list" in data
    assert "active_emergencies_list" in data
    assert "recent_audit_trail" in data
    assert data["system_status"] == "OPERATIONAL"

def test_fetch_executive_ai_summary():
    res = client.get("/api/v1/admin/executive-summary")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "metrics" in data

def test_admin_guardian_status_override():
    res = client.post("/api/v1/admin/guardians/2/override-status?status=SUSPENDED", json={
        "reason": "Administrative suspension pending safety investigation"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["overall_status"] == "SUSPENDED"

def test_fetch_filtered_audit_logs():
    res = client.get("/api/v1/admin/audit?limit=10")
    assert res.status_code == 200
    logs = res.json()
    assert isinstance(logs, list)
    assert len(logs) <= 10
