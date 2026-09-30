import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

client = TestClient(app)

def test_list_guardians():
    response = client.get("/api/v1/guardians")
    assert response.status_code == 200
    guardians = response.json()
    assert isinstance(guardians, list)
    assert len(guardians) > 0

def test_create_and_update_booking():
    # 1. Create booking
    payload = {
        "parent_id": 1,
        "guardian_id": 1,
        "parent_name": "Sarah Jenkins",
        "date": "2026-10-01",
        "time": "14:00 - 18:00",
        "care_type": "Afternoon Childcare",
        "notes": "Test booking instructions"
    }
    create_res = client.post("/api/v1/bookings", json=payload)
    assert create_res.status_code == 200
    b_data = create_res.json()
    assert b_data["status"] == "REQUESTED"
    booking_id = b_data["id"]

    # 2. Accept booking
    accept_res = client.post(f"/api/v1/bookings/{booking_id}/accept")
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "ACCEPTED"

    # 3. Check-in care session
    checkin_res = client.post("/api/v1/care-sessions/check-in", json={"booking_id": booking_id, "guardian_id": 1})
    assert checkin_res.status_code == 200
    assert checkin_res.json()["status"] == "IN_PROGRESS"

    # 4. Submit routine log
    routine_res = client.post("/api/v1/care/routine", json={
        "session_id": checkin_res.json()["id"],
        "guardian_id": 1,
        "category": "meal",
        "title": "Test Meal",
        "details": "Healthy lunch served"
    })
    assert routine_res.status_code == 200

    # 5. Check-out care session
    checkout_res = client.post("/api/v1/care-sessions/check-out", json={"booking_id": booking_id, "guardian_id": 1})
    assert checkout_res.status_code == 200
    assert checkout_res.json()["status"] == "COMPLETED"

def test_decline_booking():
    # Create booking to decline
    payload = {
        "parent_id": 1,
        "guardian_id": 2,
        "parent_name": "Sarah Jenkins",
        "date": "2026-10-02",
        "time": "10:00 - 12:00",
        "care_type": "Specialized Care",
        "notes": "Decline test"
    }
    res = client.post("/api/v1/bookings", json=payload)
    booking_id = res.json()["id"]

    decline_res = client.post(f"/api/v1/bookings/{booking_id}/decline")
    assert decline_res.status_code == 200
    assert decline_res.json()["status"] == "CANCELLED"
