import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

client = TestClient(app)

def test_sos_trigger():
    res = client.post("/api/v1/safety/sos", json={
        "user_id": 1,
        "guardian_id": 1,
        "notes": "Test emergency SOS trigger"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["event_type"] == "SOS"
    assert data["severity"] == "CRITICAL"

def test_beacon_simulation_and_status():
    # 1. Fetch status
    status_res = client.get("/api/v1/beacon/status")
    assert status_res.status_code == 200

    # 2. Simulate breach
    breach_res = client.post("/api/v1/beacon/simulate", json={"action": "breach"})
    assert breach_res.status_code == 200
    assert breach_res.json()["in_safe_zone"] == 0

    # 3. Simulate reset
    reset_res = client.post("/api/v1/beacon/simulate", json={"action": "reset"})
    assert reset_res.status_code == 200
    assert reset_res.json()["in_safe_zone"] == 1

def test_ai_assistants():
    # 1. User AI
    user_ai_res = client.post("/api/v1/ai/assistant/user", json={"prompt": "How do I book a guardian?"})
    assert user_ai_res.status_code == 200
    assert "response" in user_ai_res.json()

    # 2. Guardian AI
    g_ai_res = client.post("/api/v1/ai/assistant/guardian", json={"prompt": "What should I do if the child falls?"})
    assert g_ai_res.status_code == 200
    assert "response" in g_ai_res.json()
