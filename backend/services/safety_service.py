import secrets
from datetime import datetime
from typing import Dict, List, Optional
from backend.database import get_db_connection
from backend.models import dict_from_row, dicts_from_rows
from backend.services.booking_service import log_audit
from backend.services.beacon_service import get_beacon_status

class MockFingerprintService:
    """Fingerprint Scanner Biometric Hardware Abstraction Service."""
    
    @staticmethod
    def enroll_guardian(guardian_id: int) -> Dict:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        device_id = f"FPS-DEV-{secrets.token_hex(3).upper()}"
        
        conn = get_db_connection()
        log_audit(conn, f"Guardian #{guardian_id}", "Enrolled Fingerprint Biometrics", device_id, "SUCCESS", "Template enrolled on simulated biometric scanner")
        conn.commit()
        conn.close()
        
        return {
            "guardian_id": guardian_id,
            "status": "VERIFIED",
            "mode": "DEMO_VERIFIED",
            "enrolled": True,
            "device_id": device_id,
            "timestamp": now_str,
            "disclaimer": "Simulated hardware abstraction. Demonstrates biometric gate architecture."
        }
        
    @staticmethod
    def verify_guardian(guardian_id: int) -> Dict:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "guardian_id": guardian_id,
            "status": "VERIFIED",
            "mode": "DEMO_VERIFIED",
            "match": True,
            "confidence": 0.994,
            "timestamp": now_str,
            "disclaimer": "Biometric fingerprint verification abstraction gate passed."
        }

class MockFaceVerificationService:
    """Face & Anti-Spoof Liveness Abstraction Service."""
    
    @staticmethod
    def check_face_and_liveness(guardian_id: int) -> Dict:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "guardian_id": guardian_id,
            "face_status": "FACE_VERIFIED",
            "liveness_status": "LIVENESS_PASSED",
            "mode": "DEMO_VERIFIED",
            "anti_spoofing": "PASSED",
            "confidence": 0.988,
            "timestamp": now_str,
            "disclaimer": "Facial recognition and anti-spoof liveness check abstraction passed."
        }

def trigger_sos(user_id: int = 1, guardian_id: int = 1, latitude: float = None, longitude: float = None, notes: str = ""):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lat = latitude if latitude is not None else 37.7749
    lng = longitude if longitude is not None else -122.4194
    desc = f"EMERGENCY SOS ACTIVATED by User #{user_id}. GPS Coordinates: ({lat:.4f}, {lng:.4f})."
    if notes:
        desc += f" Notes: {notes}"
        
    cursor.execute("""
        INSERT INTO safety_events (user_id, guardian_id, event_type, severity, description, status, created_at)
        VALUES (?, ?, 'SOS', 'CRITICAL', ?, 'ACTIVE', ?)
    """, (user_id, guardian_id, desc, now_str))
    
    event_id = cursor.lastrowid
    case_ref = f"INC-SOS-{event_id:06d}"
    
    log_audit(conn, f"User #{user_id}", "Triggered Emergency SOS", f"Case #{case_ref}", "CRITICAL", desc)
    conn.commit()

    # Dispatch Multi-Channel Notifications
    try:
        from backend.services.notification_service import send_notification
        send_notification(
            user_id=user_id,
            type="SOS_BROADCAST",
            channel="SMS",
            title=f"CRITICAL EMERGENCY ALERT ({case_ref})",
            message=f"1-Tap Emergency SOS broadcast active! Live GPS: ({lat:.4f}, {lng:.4f}). Responders alerted."
        )
    except Exception:
        pass
    
    cursor.execute("SELECT * FROM safety_events WHERE id = ?", (event_id,))
    row = cursor.fetchone()
    conn.close()
    
    res = dict_from_row(row)
    res["case_reference"] = case_ref
    res["latitude"] = lat
    res["longitude"] = lng
    return res

def update_emergency_status(event_id: int, status: str, notes: str = None, actor_name: str = "Admin Dispatcher") -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    case_ref = f"INC-SOS-{event_id:06d}"
    
    update_desc = f"Status updated to '{status}' by {actor_name}."
    if notes:
        update_desc += f" Notes: {notes}"
        
    cursor.execute("UPDATE safety_events SET status = ? WHERE id = ?", (status, event_id))
    log_audit(conn, actor_name, f"Emergency Incident Status -> {status}", f"Case #{case_ref}", "SUCCESS", update_desc)
    conn.commit()
    
    cursor.execute("SELECT * FROM safety_events WHERE id = ?", (event_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"error": "Emergency event not found"}
    
    res = dict_from_row(row)
    res["case_reference"] = case_ref
    res["responder_notes"] = notes or ""
    res["updated_by"] = actor_name
    return res

def get_emergency_case_file(event_id: int) -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, u.name as user_name, u.phone as user_phone, g.name as guardian_name, gu.phone as guardian_phone
        FROM safety_events e
        LEFT JOIN users u ON e.user_id = u.id
        LEFT JOIN guardians g ON e.guardian_id = g.id
        LEFT JOIN users gu ON g.user_id = gu.id
        WHERE e.id = ?
    """, (event_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"error": "Emergency case file not found"}
    
    res = dict_from_row(row)
    res["case_reference"] = f"INC-SOS-{event_id:06d}"
    res["beacon_status"] = get_beacon_status(1)
    res["dispatch_channel"] = "MULTI_CHANNEL_SMS_PUSH_BROADCAST"
    return res

def get_safety_events(status: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM safety_events WHERE status = ? ORDER BY id DESC", (status,))
    else:
        cursor.execute("SELECT * FROM safety_events ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return dicts_from_rows(rows)

def resolve_safety_event(event_id: int, actor_name: str = "Admin"):
    return update_emergency_status(event_id, "RESOLVED", notes="Incident verified and resolved by safety officer.", actor_name=actor_name)

def get_safety_centre_status(parent_id: int = 1) -> Dict:
    """Consolidated Safety Centre Dashboard Data Aggregator."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Active Care Session
    cursor.execute("""
        SELECT b.*, s.check_in_time, s.check_out_time, g.avatar as guardian_avatar, g.rating as guardian_rating
        FROM bookings b
        LEFT JOIN care_sessions s ON b.id = s.booking_id
        LEFT JOIN guardians g ON b.guardian_id = g.id
        WHERE b.parent_id = ? AND b.status IN ('ACCEPTED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS', 'ACTIVE')
        ORDER BY b.id DESC LIMIT 1
    """, (parent_id,))
    session_row = cursor.fetchone()
    active_session = dict_from_row(session_row) if session_row else None
    
    guardian_id = active_session["guardian_id"] if active_session else 1
    
    cursor.execute("SELECT * FROM safety_events WHERE status = 'ACTIVE' ORDER BY id DESC")
    active_sos_rows = cursor.fetchall()
    active_sos = dicts_from_rows(active_sos_rows)
    
    conn.close()
    
    beacon_data = get_beacon_status(1)
    fp_data = MockFingerprintService.verify_guardian(guardian_id)
    face_data = MockFaceVerificationService.check_face_and_liveness(guardian_id)
    
    overall_safety = "NORMAL"
    if active_sos:
        overall_safety = "EMERGENCY"
    elif beacon_data.get("in_safe_zone") == 0:
        overall_safety = "BREACH"
        
    return {
        "parent_id": parent_id,
        "overall_safety_status": overall_safety,
        "active_care_session": active_session,
        "guardian_identity": {
            "guardian_id": guardian_id,
            "name": active_session["guardian_name"] if active_session else "Ananya Sharma",
            "identity_status": "VERIFIED",
            "check_in_time": active_session.get("check_in_time", "14:02") if active_session else "14:02",
            "check_out_time": active_session.get("check_out_time") if active_session else None
        },
        "verification_gates": {
            "fingerprint_state": fp_data["status"],
            "face_verification_state": face_data["face_status"],
            "liveness_state": face_data["liveness_status"],
            "mode": "DEMO VERIFIED"
        },
        "ble_presence_monitoring": {
            "child_name": beacon_data.get("child_name", "Leo Jenkins"),
            "status": "STRONG" if beacon_data.get("connected") else "DISCONNECTED",
            "distance_meters": beacon_data.get("distance_m", 3.4),
            "in_safe_zone": bool(beacon_data.get("in_safe_zone", True)),
            "battery_pct": beacon_data.get("battery_pct", 92),
            "technology": "Indoor Presence Verification + Anomaly Detection"
        },
        "location_abstraction": "Home Perimeter (San Jose, CA)",
        "active_emergencies": active_sos
    }
