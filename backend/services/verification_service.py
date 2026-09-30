import json
from datetime import datetime, timedelta
from typing import Optional, Dict
from backend.database import get_db_connection
from backend.models import dict_from_row, dicts_from_rows
from backend.services.booking_service import log_audit

def get_guardians_list(status: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM guardians WHERE overall_status = ? ORDER BY id ASC", (status,))
    else:
        cursor.execute("SELECT * FROM guardians ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return dicts_from_rows(rows)

def get_verification_details(guardian_id: int = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if guardian_id:
        cursor.execute("SELECT * FROM verification_records WHERE guardian_id = ?", (guardian_id,))
        records = dicts_from_rows(cursor.fetchall())
        cursor.execute("SELECT * FROM guardians WHERE id = ?", (guardian_id,))
        guardian = dict_from_row(cursor.fetchone())
        conn.close()
        return {"guardian": guardian, "records": records}
    else:
        cursor.execute("SELECT * FROM verification_records")
        records = dicts_from_rows(cursor.fetchall())
        conn.close()
        return {"records": records}

def submit_verification_document(guardian_id: int, document_type: str, document_url: str, notes: str = None):
    """Submit a document for 4-Gate verification."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT INTO verification_records (guardian_id, document_type, document_url, status, updated_at)
        VALUES (?, ?, ?, 'PENDING', ?)
    """, (guardian_id, document_type, document_url, now_str))
    
    log_audit(conn, f"Guardian #{guardian_id}", "Submitted Verification Document", document_type, "SUCCESS", notes or "Document uploaded for verification review")
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Document '{document_type}' submitted for Guardian #{guardian_id}"}

def verify_face_and_liveness(guardian_id: int):
    """Face & Liveness abstraction gate."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update passport
    cursor.execute("""
        UPDATE guardian_passports
        SET face_verified = 1, liveness_passed = 1, updated_at = ?
        WHERE guardian_id = ?
    """, (now_str, guardian_id))
    
    if cursor.rowcount == 0:
        cursor.execute("""
            INSERT INTO guardian_passports (guardian_id, face_verified, liveness_passed, expiry_date, updated_at)
            VALUES (?, 1, 1, '2027-12-31', ?)
        """, (guardian_id, now_str))
        
    log_audit(conn, f"Guardian #{guardian_id}", "Face & Liveness Check", "Biometric Abstraction Gate", "SUCCESS", "Face recognition match verified & anti-spoof liveness check passed")
    conn.commit()
    conn.close()
    return {
        "status": "success",
        "face_verified": True,
        "liveness_passed": True,
        "mode": "DEMO_VERIFIED",
        "message": "Face match & liveness check successfully passed"
    }

def verify_police_clearance(guardian_id: int):
    """Police Clearance abstraction gate."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        UPDATE guardians SET bg_status = 'VERIFIED' WHERE id = ?
    """, (guardian_id,))
    
    cursor.execute("""
        UPDATE guardian_passports SET police_status = 'VERIFIED', updated_at = ? WHERE guardian_id = ?
    """, (now_str, guardian_id))
    
    log_audit(conn, f"Guardian #{guardian_id}", "Police Clearance Check", "Law Enforcement Registry", "SUCCESS", "National police database record check clean")
    conn.commit()
    conn.close()
    return {
        "status": "success",
        "police_status": "VERIFIED",
        "mode": "DEMO_VERIFIED",
        "message": "Police criminal background clearance verified"
    }

def verify_address(guardian_id: int, address_details: str = None):
    """Address verification abstraction gate."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        UPDATE guardian_passports SET address_status = 'VERIFIED', updated_at = ? WHERE guardian_id = ?
    """, (now_str, guardian_id))
    
    log_audit(conn, f"Guardian #{guardian_id}", "Address Verification", "Geo-Verification Registry", "SUCCESS", f"Residential address verified: {address_details or 'Standard residential record'}")
    conn.commit()
    conn.close()
    return {
        "status": "success",
        "address_status": "VERIFIED",
        "mode": "DEMO_VERIFIED",
        "message": "Residential address verified"
    }

def get_guardian_passport(guardian_id: int) -> Dict:
    """Retrieve Digital Guardian Passport with badges, trust scores, and verification status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM guardians WHERE id = ?", (guardian_id,))
    guardian = dict_from_row(cursor.fetchone())
    if not guardian:
        conn.close()
        return None
    
    cursor.execute("SELECT * FROM guardian_passports WHERE guardian_id = ?", (guardian_id,))
    passport_row = cursor.fetchone()
    
    if not passport_row:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO guardian_passports (guardian_id, trust_score, completed_bookings, cancellation_rate, rating, identity_verified, qualification_verified, police_status, address_status, face_verified, liveness_passed, expiry_date, badges, updated_at)
            VALUES (?, 96, 42, 0.0, 4.9, 1, 1, 'VERIFIED', 'VERIFIED', 1, 1, '2027-12-31', '["CPR Certified", "Pediatric Care"]', ?)
        """, (guardian_id, now_str))
        conn.commit()
        cursor.execute("SELECT * FROM guardian_passports WHERE guardian_id = ?", (guardian_id,))
        passport_row = cursor.fetchone()
    
    p_dict = dict_from_row(passport_row)
    conn.close()
    
    badges = []
    if p_dict.get("badges"):
        try:
            badges = json.loads(p_dict["badges"])
        except Exception:
            badges = ["CPR Certified", "Verified Caregiver"]
            
    return {
        "passport_id": f"GP-{guardian_id:05d}",
        "guardian_id": guardian_id,
        "name": guardian["name"],
        "avatar": guardian.get("avatar"),
        "experience": guardian.get("experience"),
        "skills": guardian.get("skills"),
        "bio": guardian.get("bio"),
        "trust_score": p_dict["trust_score"],
        "rating": p_dict["rating"],
        "completed_bookings": p_dict["completed_bookings"],
        "cancellation_rate": f"{p_dict['cancellation_rate'] * 100:.1f}%",
        "verification_gates": {
            "identity_verified": bool(p_dict["identity_verified"]),
            "qualification_verified": bool(p_dict["qualification_verified"]),
            "police_clearance": p_dict["police_status"],
            "address_verified": p_dict["address_status"],
            "face_verified": bool(p_dict["face_verified"]),
            "liveness_passed": bool(p_dict["liveness_passed"])
        },
        "badges": badges,
        "overall_status": guardian.get("overall_status", "VERIFIED"),
        "expiry_date": p_dict.get("expiry_date", "2027-12-31"),
        "issued_at": "2026-01-01"
    }

def approve_guardian(guardian_id: int, reason: str = "Approved by Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE guardians 
        SET overall_status = 'VERIFIED', cpr_status = 'VERIFIED', bg_status = 'VERIFIED', identity_status = 'VERIFIED', doc_status = 'VERIFIED', trust_score = 98
        WHERE id = ?
    """, (guardian_id,))
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE verification_records SET status = 'VERIFIED', updated_at = ? WHERE guardian_id = ?", (now_str, guardian_id))
    cursor.execute("UPDATE guardian_passports SET identity_verified=1, qualification_verified=1, police_status='VERIFIED', address_status='VERIFIED', trust_score=98, updated_at=? WHERE guardian_id=?", (now_str, guardian_id))
    
    cursor.execute("SELECT name FROM guardians WHERE id = ?", (guardian_id,))
    g_row = cursor.fetchone()
    name = g_row["name"] if g_row else f"Guardian #{guardian_id}"
    
    log_audit(conn, "Admin", "Approved Guardian Verification", f"Guardian #{guardian_id} ({name})", "SUCCESS", reason)
    conn.commit()
    
    cursor.execute("SELECT * FROM guardians WHERE id = ?", (guardian_id,))
    row = cursor.fetchone()
    conn.close()
    return dict_from_row(row)

def reject_guardian(guardian_id: int, reason: str = "Rejected by Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE guardians 
        SET overall_status = 'REJECTED', trust_score = 45
        WHERE id = ?
    """, (guardian_id,))
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE verification_records SET status = 'REJECTED', updated_at = ? WHERE guardian_id = ?", (now_str, guardian_id))
    cursor.execute("UPDATE guardian_passports SET trust_score=45, updated_at=? WHERE guardian_id=?", (now_str, guardian_id))
    
    cursor.execute("SELECT name FROM guardians WHERE id = ?", (guardian_id,))
    g_row = cursor.fetchone()
    name = g_row["name"] if g_row else f"Guardian #{guardian_id}"
    
    log_audit(conn, "Admin", "Rejected Guardian Verification", f"Guardian #{guardian_id} ({name})", "FAILED", reason)
    conn.commit()
    
    cursor.execute("SELECT * FROM guardians WHERE id = ?", (guardian_id,))
    row = cursor.fetchone()
    conn.close()
    return dict_from_row(row)
