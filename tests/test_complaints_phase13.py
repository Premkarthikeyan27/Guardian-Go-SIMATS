import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

client = TestClient(app)

def test_submit_complaint_and_nlp_xai():
    req = {
        "parent_id": 1,
        "guardian_id": 2,
        "booking_id": 1,
        "complaint_text": "Caregiver arrived 20 minutes late and left the child unsupervised near the pool."
    }
    res = client.post("/api/v1/complaints", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["parent_id"] == 1
    assert data["guardian_id"] == 2
    assert "sentiment" in data
    assert "risk_level" in data
    assert "category" in data
    assert "xai_factors" in data
    assert isinstance(data["xai_factors"], list)
    assert len(data["xai_factors"]) >= 1
    assert "recommended_action" in data
    assert "nlp_metadata" in data

def test_list_all_complaints():
    res = client.get("/api/v1/complaints")
    assert res.status_code == 200
    complaints = res.json()
    assert isinstance(complaints, list)
    assert len(complaints) >= 1

def test_list_parent_and_guardian_complaints():
    p_res = client.get("/api/v1/complaints/parent/1")
    assert p_res.status_code == 200
    assert isinstance(p_res.json(), list)

    g_res = client.get("/api/v1/complaints/guardian/2")
    assert g_res.status_code == 200
    assert isinstance(g_res.json(), list)

def test_admin_resolve_complaint():
    # Submit a complaint first
    sub_res = client.post("/api/v1/complaints", json={
        "parent_id": 1,
        "guardian_id": 2,
        "complaint_text": "Caregiver arrived 10 minutes late."
    })
    comp_id = sub_res.json()["id"]

    res_req = {
        "action": "WARN_GUARDIAN",
        "admin_notes": "Official warning issued for tardiness.",
        "actor_name": "Chief Safety Officer"
    }
    resolve_res = client.post(f"/api/v1/complaints/{comp_id}/resolve", json=res_req)
    assert resolve_res.status_code == 200
    data = resolve_res.json()
    assert data["status"] == "RESOLVED"
    assert data["recommended_action"] == "WARN_GUARDIAN"
