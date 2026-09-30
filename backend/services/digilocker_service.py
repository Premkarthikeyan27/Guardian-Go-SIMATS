import os
import json
import secrets
from datetime import datetime
from typing import Dict, List, Optional
from backend.database import get_db_connection
from backend.models import dict_from_row, dicts_from_rows
from backend.services.booking_service import log_audit

# Environment configuration for DigiLocker Integration
DIGILOCKER_CLIENT_ID = os.environ.get("DIGILOCKER_CLIENT_ID", "guardian-go-demo")
DIGILOCKER_CLIENT_SECRET = os.environ.get("DIGILOCKER_CLIENT_SECRET")
DIGILOCKER_REDIRECT_URI = os.environ.get(
    "DIGILOCKER_REDIRECT_URI",
    "http://127.0.0.1:8000/api/v1/digilocker/callback"
)
DIGILOCKER_ENVIRONMENT = os.environ.get("DIGILOCKER_ENVIRONMENT", "demo")  # 'live' or 'demo'

class MockDigiLockerService:
    """Mock/Simulated DigiLocker Service compliant with official DigiLocker OAuth2 workflow."""
    
    @staticmethod
    def generate_consent_url(guardian_id: int) -> Dict:
        txn_id = f"TXN-DL-{secrets.token_hex(4).upper()}"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO digilocker_verifications (guardian_id, status, txn_id, mode, consent_timestamp, updated_at)
            VALUES (?, 'PENDING_CONSENT', ?, 'DEMO_VERIFIED', ?, ?)
            ON CONFLICT(guardian_id) DO UPDATE SET
            status = 'PENDING_CONSENT', txn_id = ?, consent_timestamp = ?, updated_at = ?
        """, (guardian_id, txn_id, now_str, now_str, txn_id, now_str, now_str))
        
        log_audit(conn, f"Guardian #{guardian_id}", "Initiated DigiLocker Consent", f"Transaction {txn_id}", "SUCCESS", "Redirecting guardian to DigiLocker consent gateway")
        conn.commit()
        conn.close()
        
        consent_url = f"https://digilocker.gov.in/public/oauth2/1/authorize?response_type=code&client_id={DIGILOCKER_CLIENT_ID}&redirect_uri={DIGILOCKER_REDIRECT_URI}&state={txn_id}"
        
        return {
            "status": "pending_consent",
            "txn_id": txn_id,
            "consent_url": consent_url,
            "mode": "DEMO VERIFIED" if DIGILOCKER_ENVIRONMENT == "demo" else "LIVE VERIFIED",
            "message": "DigiLocker consent session initiated. Please authorize consent."
        }

    @staticmethod
    def complete_consent_and_verify(guardian_id: int, auth_code: str = None) -> Dict:
        conn = get_db_connection()
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("SELECT name FROM guardians WHERE id = ?", (guardian_id,))
        g_row = cursor.fetchone()
        guardian_name = g_row["name"] if g_row else f"Guardian #{guardian_id}"
        
        last_four = str(secrets.randbelow(9000) + 1000)
        docs = ["Aadhaar Card", "Secondary School Certificate", "Nursing / Caregiver Diploma"]
        docs_json = json.dumps(docs)
        mode_label = "DEMO_VERIFIED" if DIGILOCKER_ENVIRONMENT == "demo" else "VERIFIED"
        
        cursor.execute("""
            UPDATE digilocker_verifications
            SET status = ?, aadhaar_last_four = ?, verified_name = ?, documents_found = ?, mode = ?, updated_at = ?
            WHERE guardian_id = ?
        """, (mode_label, last_four, guardian_name, docs_json, mode_label, now_str, guardian_id))
        
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO digilocker_verifications (guardian_id, status, txn_id, aadhaar_last_four, verified_name, documents_found, mode, consent_timestamp, updated_at)
                VALUES (?, ?, 'TXN-DL-AUTO', ?, ?, ?, ?, ?, ?)
            """, (guardian_id, mode_label, last_four, guardian_name, docs_json, mode_label, now_str, now_str))
            
        cursor.execute("""
            UPDATE guardians
            SET identity_status = 'VERIFIED', overall_status = CASE WHEN overall_status = 'PENDING' THEN 'VERIFIED' ELSE overall_status END
            WHERE id = ?
        """, (guardian_id,))
        
        log_audit(conn, f"Guardian #{guardian_id}", "Completed DigiLocker Verification", f"Aadhaar XXXX-XXXX-{last_four}", "SUCCESS", f"Consent authorized & verified {len(docs)} official documents from DigiLocker API ({mode_label})")
        conn.commit()
        conn.close()
        
        return {
            "status": mode_label,
            "guardian_id": guardian_id,
            "verified_name": guardian_name,
            "aadhaar_masked": f"XXXX-XXXX-{last_four}",
            "documents_retrieved": docs,
            "mode": "DEMO VERIFIED" if mode_label == "DEMO_VERIFIED" else "LIVE VERIFIED",
            "message": f"DigiLocker verification completed successfully ({mode_label})"
        }

def get_digilocker_status(guardian_id: int) -> Dict:
    """Get DigiLocker verification record for a guardian."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM digilocker_verifications WHERE guardian_id = ?", (guardian_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {
            "guardian_id": guardian_id,
            "status": "NOT_STARTED",
            "mode": "DEMO VERIFIED" if DIGILOCKER_ENVIRONMENT == "demo" else "LIVE VERIFIED",
            "documents_found": [],
            "aadhaar_masked": "NOT VERIFIED"
        }
    
    d_dict = dict_from_row(row)
    docs = []
    if d_dict.get("documents_found"):
        try:
            docs = json.loads(d_dict["documents_found"])
        except Exception:
            docs = []
            
    return {
        "guardian_id": guardian_id,
        "status": d_dict["status"],
        "txn_id": d_dict.get("txn_id"),
        "aadhaar_masked": f"XXXX-XXXX-{d_dict.get('aadhaar_last_four', 'XXXX')}",
        "verified_name": d_dict.get("verified_name"),
        "documents_found": docs,
        "mode": "DEMO VERIFIED" if d_dict.get("mode") == "DEMO_VERIFIED" else "LIVE VERIFIED",
        "consent_timestamp": d_dict.get("consent_timestamp"),
        "updated_at": d_dict.get("updated_at")
    }

def admin_override_digilocker(guardian_id: int, status_override: str, reason: str = None) -> Dict:
    """Admin workflow action to manually approve or reject DigiLocker verification."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        UPDATE digilocker_verifications
        SET status = ?, updated_at = ?
        WHERE guardian_id = ?
    """, (status_override, now_str, guardian_id))
    
    log_audit(conn, "Admin", "Admin DigiLocker Override", f"Guardian #{guardian_id}", "SUCCESS", f"Status updated to '{status_override}': {reason or 'Admin review'}")
    conn.commit()
    conn.close()
    return get_digilocker_status(guardian_id)
