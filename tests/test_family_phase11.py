import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

client = TestClient(app)

def test_fetch_family_members():
    res = client.get("/api/v1/family/members/1")
    assert res.status_code == 200
    members = res.json()
    assert isinstance(members, list)
    assert len(members) >= 1

def test_invite_family_member():
    req = {
        "parent_id": 1,
        "name": "Mark Jenkins",
        "email": "uncle_mark@demo.com",
        "relation": "Uncle / Co-Parent",
        "access_level": "FULL_ACCESS"
    }
    res = client.post("/api/v1/family/members", json=req)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Mark Jenkins"
    assert data["relation"] == "Uncle / Co-Parent"
    assert data["access_level"] == "FULL_ACCESS"
    assert data["status"] == "ACTIVE"

def test_delete_family_member():
    # Invite temporary member
    invite_res = client.post("/api/v1/family/members", json={
        "parent_id": 1,
        "name": "Temp Cousin",
        "email": "temp@demo.com",
        "relation": "Cousin",
        "access_level": "CARE_VIEWER"
    })
    member_id = invite_res.json()["id"]

    del_res = client.delete(f"/api/v1/family/members/{member_id}?parent_id=1")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "REMOVED"

def test_post_and_fetch_care_routines():
    req = {
        "session_id": 1,
        "guardian_id": 1,
        "category": "medication",
        "title": "Evening Pediatric Vitamin",
        "details": "Administered 1 vitamin chew with water."
    }
    post_res = client.post("/api/v1/family/routines", json=req)
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["category"] == "medication"
    assert data["title"] == "Evening Pediatric Vitamin"

    # Fetch routines for session
    session_res = client.get("/api/v1/family/routines/session/1")
    assert session_res.status_code == 200
    routines = session_res.json()
    assert any(r["title"] == "Evening Pediatric Vitamin" for r in routines)

    # Fetch routines for guardian
    guardian_res = client.get("/api/v1/family/routines/guardian/1")
    assert guardian_res.status_code == 200
    g_routines = guardian_res.json()
    assert len(g_routines) >= 1
