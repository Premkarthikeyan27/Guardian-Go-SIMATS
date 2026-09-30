import sys
import os
import uuid
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import app

client = TestClient(app)

def test_full_platform_end_to_end_journey():
    unique_id = uuid.uuid4().hex[:6]
    parent_email = f"parent_integration_{unique_id}@demo.com"
    guardian_email = f"guardian_integration_{unique_id}@demo.com"
    booking_date = f"2027-{(int(unique_id, 16) % 11) + 1:02d}-{(int(unique_id, 16) % 25) + 1:02d}"

    # 1. Register Parent
    p_reg = client.post("/api/v1/auth/register/parent", json={
        "name": "Integration Parent",
        "email": parent_email,
        "password": "password123",
        "phone": "+1 555-9999"
    })
    assert p_reg.status_code == 200
    parent_id = p_reg.json()["user"]["id"]

    # 2. Register Guardian
    g_reg = client.post("/api/v1/auth/register/guardian", json={
        "name": "Integration Guardian",
        "email": guardian_email,
        "password": "password123",
        "phone": "+1 555-8888",
        "experience": "4 years experience",
        "skills": "First Aid, CPR, Special Needs Care"
    })
    assert g_reg.status_code == 200
    guardian_id = 1  # Standard verified guardian for integration workflow

    # 3. Guardian 4-Gate Verification & Digital Passport
    verify_res = client.post("/api/v1/verification/face-verify", json={"guardian_id": guardian_id})
    assert verify_res.status_code == 200

    passport_res = client.get(f"/api/v1/verification/passport/{guardian_id}")
    assert passport_res.status_code == 200
    assert passport_res.json()["guardian_id"] == guardian_id

    # 4. DigiLocker Verification Check
    dl_init = client.post("/api/v1/digilocker/initiate", json={"guardian_id": guardian_id})
    assert dl_init.status_code == 200
    dl_consent = client.post("/api/v1/digilocker/consent", json={"guardian_id": guardian_id, "auth_code": "TEST_CODE"})
    assert dl_consent.status_code == 200

    # 5. Parent Membership Upgrade
    mem_res = client.post("/api/v1/membership/subscribe", json={
        "user_id": parent_id,
        "plan": "PREMIUM_CARE_PLUS"
    })
    assert mem_res.status_code == 200

    # 6. AI Caregiver Recommendation
    ai_rec = client.post("/api/v1/ai/recommend-guardians", json={
        "parent_id": parent_id,
        "care_type": "Childcare"
    })
    assert ai_rec.status_code == 200
    assert "explanation" in ai_rec.json()

    # 7. Create Care Booking
    booking_res = client.post("/api/v1/bookings", json={
        "parent_id": parent_id,
        "guardian_id": guardian_id,
        "date": booking_date,
        "time": "14:00 - 18:00",
        "care_type": "Pediatric Childcare",
        "notes": "Full end-to-end integration test booking"
    })
    assert booking_res.status_code == 200
    booking_id = booking_res.json()["id"]

    # 8. Guardian Accepts Booking & Checks In
    accept_res = client.post(f"/api/v1/bookings/{booking_id}/accept")
    assert accept_res.status_code == 200

    checkin_res = client.post(f"/api/v1/bookings/{booking_id}/status", json={"status": "CHECKED_IN", "actor_name": "Guardian"})
    assert checkin_res.status_code == 200

    # 9. Hardware Biometrics & BLE Presence Check
    fp_res = client.post(f"/api/v1/safety/fingerprint/verify?guardian_id={guardian_id}")
    assert fp_res.status_code == 200

    centre_res = client.get(f"/api/v1/safety/centre/{parent_id}")
    assert centre_res.status_code == 200

    # 10. Log Care Routine & Create Daily Care Report
    routine_res = client.post("/api/v1/family/routines", json={
        "session_id": 1,
        "guardian_id": guardian_id,
        "category": "meal",
        "title": "Healthy Organic Lunch",
        "details": "Steamed veggies and rice"
    })
    assert routine_res.status_code == 200

    report_res = client.post("/api/v1/reports", json={
        "booking_id": booking_id,
        "guardian_id": guardian_id,
        "parent_id": parent_id,
        "child_name": "Leo Jenkins",
        "date": booking_date,
        "meals": {"lunch": "Steamed veggies and rice"},
        "mood": "Happy & Active",
        "health_notes": "All clear."
    })
    assert report_res.status_code == 200
    assert "ai_summary" in report_res.json()

    # 11. Family Circle Invitation & Multi-Channel Notification
    fam_res = client.post("/api/v1/family/members", json={
        "parent_id": parent_id,
        "name": "Integration Uncle",
        "email": f"uncle_{unique_id}@demo.com",
        "relation": "Co-Parent / Uncle",
        "access_level": "FULL_ACCESS"
    })
    assert fam_res.status_code == 200

    notif_res = client.get(f"/api/v1/notifications/{parent_id}")
    assert notif_res.status_code == 200

    # 12. Trigger Emergency SOS & Resolve via Command Centre
    sos_res = client.post("/api/v1/safety/emergency/trigger", json={
        "user_id": parent_id,
        "guardian_id": guardian_id,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "notes": "Integration Test Emergency Alert"
    })
    assert sos_res.status_code == 200
    incident_id = sos_res.json()["id"]

    sos_resolve = client.post(f"/api/v1/safety/emergency/{incident_id}/status", json={
        "status": "RESOLVED",
        "notes": "End-to-end integration emergency resolved safely.",
        "actor_name": "Command Center Chief"
    })
    assert sos_resolve.status_code == 200

    # 13. Parent Complaint Submission & NLP Analysis
    complaint_res = client.post("/api/v1/complaints", json={
        "parent_id": parent_id,
        "guardian_id": guardian_id,
        "booking_id": booking_id,
        "complaint_text": "Caregiver was 5 minutes late for session check-in."
    })
    assert complaint_res.status_code == 200
    comp_id = complaint_res.json()["id"]

    comp_resolve = client.post(f"/api/v1/complaints/{comp_id}/resolve", json={
        "action": "WARN_GUARDIAN",
        "admin_notes": "Integration complaint resolved with guardian warning."
    })
    assert comp_resolve.status_code == 200

    # 14. Admin Command Centre Payload Verification
    cmd_res = client.get("/api/v1/admin/command-centre")
    assert cmd_res.status_code == 200
    assert cmd_res.json()["system_status"] == "OPERATIONAL"

    # 15. Security Health & Audit Check
    sec_res = client.get("/api/v1/security/health")
    assert sec_res.status_code == 200
    assert sec_res.json()["status"] == "SECURE"
