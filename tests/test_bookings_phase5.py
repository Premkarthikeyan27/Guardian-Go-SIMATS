import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import init_db, seed_db

client = TestClient(app)

def setup_module():
    init_db()
    seed_db()

def test_search_guardians():
    res = client.get("/api/v1/bookings/guardians/search?query=CPR")
    assert res.status_code == 200
    guardians = res.json()
    assert isinstance(guardians, list)
    assert len(guardians) >= 1

def test_guardian_availability_management():
    # Set availability
    res_set = client.post("/api/v1/bookings/availability", json={
        "guardian_id": 1,
        "date": "2026-10-15",
        "time_slots": ["09:00 - 12:00", "13:00 - 17:00"],
        "service_types": ["Pediatric Care", "Infant Care"],
        "specialization": "Pediatric Nurse"
    })
    assert res_set.status_code == 200
    
    # Get availability
    res_get = client.get("/api/v1/bookings/availability/1?date=2026-10-15")
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["guardian_id"] == 1
    assert len(data["availability"]) >= 1

def test_create_booking_and_conflict_prevention():
    import uuid
    date_str = f"2026-11-{uuid.uuid4().hex[:4]}"
    time_str = "10:00 - 14:00"
    
    # First booking should succeed
    res1 = client.post("/api/v1/bookings", json={
        "parent_id": 1,
        "guardian_id": 1,
        "parent_name": "Sarah Jenkins",
        "date": date_str,
        "time": time_str,
        "care_type": "Standard Care",
        "notes": "First booking test"
    })
    assert res1.status_code == 200
    booking1 = res1.json()
    assert booking1["status"] == "REQUESTED"

    # Second booking for SAME guardian on SAME date & time must fail with 409 Conflict
    res2 = client.post("/api/v1/bookings", json={
        "parent_id": 1,
        "guardian_id": 1,
        "parent_name": "Sarah Jenkins",
        "date": date_str,
        "time": time_str,
        "care_type": "Standard Care",
        "notes": "Duplicate booking attempt"
    })
    assert res2.status_code == 409
    assert "Conflict" in res2.json()["detail"]

def test_booking_lifecycle_transitions():
    import uuid
    date_str = f"2026-12-{uuid.uuid4().hex[:4]}"
    # Create booking
    res = client.post("/api/v1/bookings", json={
        "parent_id": 1,
        "guardian_id": 3,
        "parent_name": "Sarah Jenkins",
        "date": date_str,
        "time": "09:00 - 12:00",
        "care_type": "Infant Care"
    })
    assert res.status_code == 200
    b_id = res.json()["id"]

    # Accept booking
    res_acc = client.post(f"/api/v1/bookings/{b_id}/accept")
    assert res_acc.status_code == 200
    assert res_acc.json()["status"] == "ACCEPTED"

    # Status update to CONFIRMED
    res_conf = client.post(f"/api/v1/bookings/{b_id}/status", json={"status": "CONFIRMED"})
    assert res_conf.status_code == 200
    assert res_conf.json()["status"] == "CONFIRMED"

def test_list_bookings_filtered():
    res = client.get("/api/v1/bookings?role=parent&user_id=1")
    assert res.status_code == 200
    bookings = res.json()
    assert isinstance(bookings, list)
    assert len(bookings) >= 1
