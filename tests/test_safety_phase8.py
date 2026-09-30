import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

client = TestClient(app)

def test_safety_centre_dashboard():
    res = client.get("/api/v1/safety/centre/1")
    assert res.status_code == 200
    data = res.json()
    assert "overall_safety_status" in data
    assert "verification_gates" in data
    assert "ble_presence_monitoring" in data
    assert data["ble_presence_monitoring"]["technology"] == "Indoor Presence Verification + Anomaly Detection"
    assert "fingerprint_state" in data["verification_gates"]
    assert "face_verification_state" in data["verification_gates"]

def test_biometric_fingerprint_enroll_and_verify():
    enroll_res = client.post("/api/v1/safety/fingerprint/enroll?guardian_id=1")
    assert enroll_res.status_code == 200
    enroll_data = enroll_res.json()
    assert enroll_data["status"] == "VERIFIED"
    assert enroll_data["enrolled"] is True
    assert "device_id" in enroll_data

    verify_res = client.post("/api/v1/safety/fingerprint/verify?guardian_id=1")
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["status"] == "VERIFIED"
    assert verify_data["match"] is True

def test_face_and_liveness_check():
    res = client.post("/api/v1/safety/face/liveness?guardian_id=1")
    assert res.status_code == 200
    data = res.json()
    assert data["face_status"] == "FACE_VERIFIED"
    assert data["liveness_status"] == "LIVENESS_PASSED"

def test_sos_and_event_resolution():
    sos_res = client.post("/api/v1/safety/sos", json={
        "user_id": 1,
        "guardian_id": 1,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "notes": "Test Phase 8 Emergency Alert"
    })
    assert sos_res.status_code == 200
    sos_data = sos_res.json()
    assert sos_data["event_type"] == "SOS"
    assert sos_data["status"] == "ACTIVE"
    event_id = sos_data["id"]

    events_res = client.get("/api/v1/safety/events?status=ACTIVE")
    assert events_res.status_code == 200
    assert any(e["id"] == event_id for e in events_res.json())

    resolve_res = client.post(f"/api/v1/safety/events/{event_id}/resolve")
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"
