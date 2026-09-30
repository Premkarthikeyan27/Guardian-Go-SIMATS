import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, seed_db

client = TestClient(app)

def setup_module():
    init_db()
    seed_db()

def test_digilocker_initiate_consent():
    res = client.post("/api/v1/digilocker/initiate", json={"guardian_id": 1})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "pending_consent"
    assert "txn_id" in data
    assert "consent_url" in data
    assert "digilocker.gov.in" in data["consent_url"]
    assert "mode" in data

def test_digilocker_complete_consent():
    res = client.post("/api/v1/digilocker/consent", json={
        "guardian_id": 1,
        "auth_code": "MOCK_OAUTH_CODE_2026"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["DEMO_VERIFIED", "VERIFIED"]
    assert data["guardian_id"] == 1
    assert "aadhaar_masked" in data
    assert "XXXX-XXXX-" in data["aadhaar_masked"]
    assert len(data["documents_retrieved"]) > 0

def test_digilocker_status_query():
    res = client.get("/api/v1/digilocker/status/1")
    assert res.status_code == 200
    data = res.json()
    assert data["guardian_id"] == 1
    assert data["status"] in ["DEMO_VERIFIED", "VERIFIED"]
    assert "mode" in data

def test_digilocker_documents_query():
    res = client.get("/api/v1/digilocker/documents/1")
    assert res.status_code == 200
    data = res.json()
    assert data["guardian_id"] == 1
    assert "documents" in data
    assert isinstance(data["documents"], list)

def test_admin_digilocker_verify_override():
    res = client.post("/api/v1/digilocker/admin/verify", json={
        "guardian_id": 1,
        "status_override": "VERIFIED",
        "reason": "Official document audit verified by admin"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "VERIFIED"
