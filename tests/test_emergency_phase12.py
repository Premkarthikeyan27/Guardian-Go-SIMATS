import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

client = TestClient(app)

def test_emergency_trigger_and_case_reference():
    req = {
        "user_id": 1,
        "guardian_id": 1,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "notes": "Phase 12 Emergency 1-Tap Trigger Test"
    }
    res = client.post("/api/v1/safety/emergency/trigger", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["event_type"] == "SOS"
    assert data["severity"] == "CRITICAL"
    assert "case_reference" in data
    assert data["case_reference"].startswith("INC-SOS-")
    assert data["status"] == "ACTIVE"

def test_fetch_active_emergencies():
    res = client.get("/api/v1/safety/emergency/active")
    assert res.status_code == 200
    active_events = res.json()
    assert isinstance(active_events, list)
    assert len(active_events) >= 1

def test_fetch_emergency_case_file():
    # Trigger an emergency first
    trigger_res = client.post("/api/v1/safety/emergency/trigger", json={
        "user_id": 1,
        "guardian_id": 1,
        "notes": "Emergency Case File Inspection"
    })
    incident_id = trigger_res.json()["id"]

    case_res = client.get(f"/api/v1/safety/emergency/{incident_id}")
    assert case_res.status_code == 200
    case_data = case_res.json()
    assert case_data["id"] == incident_id
    assert "case_reference" in case_data
    assert "beacon_status" in case_data
    assert case_data["dispatch_channel"] == "MULTI_CHANNEL_SMS_PUSH_BROADCAST"

def test_emergency_state_transitions():
    # Trigger incident
    trigger_res = client.post("/api/v1/safety/emergency/trigger", json={
        "user_id": 1,
        "guardian_id": 1,
        "notes": "State transition test"
    })
    incident_id = trigger_res.json()["id"]

    # 1. Transition -> DISPATCHED
    d_res = client.post(f"/api/v1/safety/emergency/{incident_id}/status", json={
        "status": "DISPATCHED",
        "notes": "Emergency Response Unit dispatched to location",
        "actor_name": "Chief Dispatcher"
    })
    assert d_res.status_code == 200
    assert d_res.json()["status"] == "DISPATCHED"

    # 2. Transition -> RESPONDER_ON_SCENE
    r_res = client.post(f"/api/v1/safety/emergency/{incident_id}/status", json={
        "status": "RESPONDER_ON_SCENE",
        "notes": "First Responders arrived at home perimeter",
        "actor_name": "Officer Davies"
    })
    assert r_res.status_code == 200
    assert r_res.json()["status"] == "RESPONDER_ON_SCENE"

    # 3. Transition -> RESOLVED
    res_res = client.post(f"/api/v1/safety/emergency/{incident_id}/status", json={
        "status": "RESOLVED",
        "notes": "Situation verified safe. Child and caregiver secure.",
        "actor_name": "Chief Dispatcher"
    })
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "RESOLVED"
