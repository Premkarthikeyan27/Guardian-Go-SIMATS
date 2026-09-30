import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, seed_db

client = TestClient(app)

def setup_module():
    init_db()
    seed_db()

def test_get_guardian_passport():
    response = client.get("/api/v1/verification/passport/1")
    assert response.status_code == 200
    passport = response.json()
    assert passport["passport_id"] == "GP-00001"
    assert passport["guardian_id"] == 1
    assert passport["name"] == "Ananya Sharma"
    assert "verification_gates" in passport
    assert passport["verification_gates"]["identity_verified"] is True
    assert passport["verification_gates"]["police_clearance"] == "VERIFIED"
    assert "badges" in passport
    assert len(passport["badges"]) > 0

def test_upload_verification_document():
    res = client.post("/api/v1/verification/upload", json={
        "guardian_id": 1,
        "document_type": "First Aid Refresh Certificate",
        "document_url": "https://example.com/docs/cpr_renew.pdf",
        "notes": "Renewed CPR certification"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "success"

def test_face_and_liveness_check():
    res = client.post("/api/v1/verification/face-verify", json={"guardian_id": 1})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["face_verified"] is True
    assert data["liveness_passed"] is True

def test_police_clearance_check():
    res = client.post("/api/v1/verification/police-verify", json={"guardian_id": 1})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["police_status"] == "VERIFIED"

def test_address_verification_check():
    res = client.post("/api/v1/verification/address-verify", json={
        "guardian_id": 1,
        "address_details": "124 Park View Lane, San Jose, CA"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["address_status"] == "VERIFIED"

def test_verification_status_checklist():
    res = client.get("/api/v1/verification/status/1")
    assert res.status_code == 200
    data = res.json()
    assert "guardian" in data
    assert "records" in data
    assert len(data["records"]) > 0
