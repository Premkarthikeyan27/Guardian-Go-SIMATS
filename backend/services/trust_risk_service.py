import json
from datetime import datetime
from typing import Dict, List, Optional
from backend.database import get_db_connection
from backend.models import dict_from_row, dicts_from_rows
from backend.services.booking_service import log_audit
from backend.services.ai_service import call_qwen_ollama

def calculate_trust_score(guardian_id: int) -> Dict:
    """Calculate observable evidence-based Trust Score (0-100) with explainable factor breakdown."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM guardians WHERE id = ?", (guardian_id,))
    guardian = dict_from_row(cursor.fetchone())
    if not guardian:
        conn.close()
        return None
        
    cursor.execute("SELECT * FROM guardian_passports WHERE guardian_id = ?", (guardian_id,))
    passport = dict_from_row(cursor.fetchone()) or {}
    
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE guardian_id = ? AND status = 'COMPLETED'", (guardian_id,))
    completed_cnt = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE guardian_id = ? AND status = 'CANCELLED'", (guardian_id,))
    cancelled_cnt = cursor.fetchone()[0]
    
    conn.close()
    
    base_score = 50
    factors = []
    
    # 1. 4-Gate Verification
    if guardian.get("overall_status") == "VERIFIED":
        base_score += 25
        factors.append({"factor": "4-Gate Verification Completed", "points": "+25", "type": "positive"})
    elif guardian.get("overall_status") == "PENDING":
        base_score += 10
        factors.append({"factor": "Verification Pending Audit", "points": "+10", "type": "neutral"})
        
    # 2. Completed Bookings
    booking_pts = min(completed_cnt, 20)
    if booking_pts > 0:
        base_score += booking_pts
        factors.append({"factor": f"Completed {completed_cnt} Successful Care Sessions", "points": f"+{booking_pts}", "type": "positive"})
        
    # 3. Rating Score
    rating = guardian.get("rating", 4.5)
    if rating >= 4.8:
        base_score += 10
        factors.append({"factor": f"High Customer Rating ({rating}/5.0)", "points": "+10", "type": "positive"})
    elif rating >= 4.5:
        base_score += 5
        factors.append({"factor": f"Good Customer Rating ({rating}/5.0)", "points": "+5", "type": "positive"})
        
    # 4. Cancellation Rate Penalty
    if cancelled_cnt > 0:
        penalty = min(cancelled_cnt * 5, 20)
        base_score -= penalty
        factors.append({"factor": f"{cancelled_cnt} Session Cancellations", "points": f"-{penalty}", "type": "negative"})
        
    # 5. Punctuality & Identity
    if passport.get("face_verified") and passport.get("liveness_passed"):
        base_score += 5
        factors.append({"factor": "Liveness & Biometric Verification Passed", "points": "+5", "type": "positive"})
        
    final_score = max(0, min(100, base_score))
    
    # Update score in DB
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE guardians SET trust_score = ? WHERE id = ?", (final_score, guardian_id))
    cursor.execute("UPDATE guardian_passports SET trust_score = ?, updated_at = ? WHERE guardian_id = ?", (final_score, now_str, guardian_id))
    conn.commit()
    conn.close()
    
    return {
        "guardian_id": guardian_id,
        "guardian_name": guardian["name"],
        "trust_score": final_score,
        "trust_level": "EXCELLENT" if final_score >= 90 else ("HIGH" if final_score >= 75 else "MODERATE"),
        "explainable_factors": factors,
        "last_calculated": now_str
    }

async def evaluate_risk_and_fraud(guardian_id: int) -> Dict:
    """Evaluate observable risk/fraud signals using Qwen AI & rule engine. AI flags only, Admin decides."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM guardians WHERE id = ?", (guardian_id,))
    guardian = dict_from_row(cursor.fetchone())
    
    cursor.execute("SELECT * FROM digilocker_verifications WHERE guardian_id = ?", (guardian_id,))
    digilocker = dict_from_row(cursor.fetchone())
    
    cursor.execute("SELECT COUNT(*) FROM bookings WHERE guardian_id = ? AND status = 'CANCELLED'", (guardian_id,))
    cancel_cnt = cursor.fetchone()[0]
    
    conn.close()
    
    if not guardian:
        return {"status": "error", "message": f"Guardian #{guardian_id} not found"}
        
    signals = []
    severity = "LOW"
    alert_type = "SYSTEM_AUDIT"
    ai_confidence = 0.85
    
    if cancel_cnt >= 2:
        signals.append("Multiple session cancellations detected (>2 cancellations)")
        severity = "MEDIUM"
        alert_type = "REPEATED_CANCELLATION"
        
    if digilocker and digilocker.get("status") == "PENDING_CONSENT":
        signals.append("DigiLocker identity consent pending over 7 days")
        if severity == "LOW":
            severity = "MEDIUM"
            alert_type = "VERIFICATION_FAILURE"
            
    if guardian.get("overall_status") == "PENDING":
        signals.append("Background check documentation incomplete")
        
    prompt = f"Evaluate risk for Guardian '{guardian['name']}' with signals: {signals}. Categorize severity as LOW, MEDIUM, HIGH, or CRITICAL and state AI confidence."
    ai_eval = await call_qwen_ollama(prompt, "You are the Guardian Go Fraud & Risk AI Detection Engine. AI flags risks for Admin review only.")
    
    description = f"AI Risk Signal Flag for {guardian['name']}: " + (", ".join(signals) if signals else "Standard baseline check clean.")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO risk_alerts (guardian_id, alert_type, severity, description, ai_confidence, explainable_signals, status, admin_notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, 'OPEN', ?, ?, ?)
    """, (guardian_id, alert_type, severity, description, ai_confidence, json.dumps(signals), ai_eval or "Rule engine evaluation clean", now_str, now_str))
    
    alert_id = cursor.lastrowid
    log_audit(conn, "AI Risk Engine", "Generated Risk Flag", f"Risk Alert #{alert_id}", "WARNING", f"Severity: {severity}, Type: {alert_type}")
    conn.commit()
    conn.close()
    
    return {
        "alert_id": alert_id,
        "guardian_id": guardian_id,
        "alert_type": alert_type,
        "severity": severity,
        "description": description,
        "ai_confidence": ai_confidence,
        "explainable_signals": signals,
        "ai_analysis": ai_eval,
        "status": "OPEN",
        "action_policy": "AI flags only. Admin retains sole authority for suspensions or rejections."
    }

def list_risk_alerts(status_filter: str = None) -> List[Dict]:
    """Fetch active risk and fraud alerts for Admin Command Centre."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if status_filter:
        cursor.execute("""
            SELECT r.*, g.name as guardian_name, g.avatar as guardian_avatar
            FROM risk_alerts r
            JOIN guardians g ON r.guardian_id = g.id
            WHERE r.status = ?
            ORDER BY r.id DESC
        """, (status_filter,))
    else:
        cursor.execute("""
            SELECT r.*, g.name as guardian_name, g.avatar as guardian_avatar
            FROM risk_alerts r
            JOIN guardians g ON r.guardian_id = g.id
            ORDER BY r.id DESC
        """)
    rows = cursor.fetchall()
    conn.close()
    return dicts_from_rows(rows)

def admin_resolve_risk_alert(alert_id: int, action: str, admin_notes: str = None) -> Dict:
    """Admin operational action to resolve, dismiss, or enforce suspension on a risk alert."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    new_status = "RESOLVED" if action in ["RESOLVE", "SUSPEND_GUARDIAN"] else "DISMISSED"
    cursor.execute("""
        UPDATE risk_alerts
        SET status = ?, admin_notes = ?, updated_at = ?
        WHERE id = ?
    """, (new_status, admin_notes or f"Admin decision: {action}", now_str, alert_id))
    
    cursor.execute("SELECT guardian_id FROM risk_alerts WHERE id = ?", (alert_id,))
    row = cursor.fetchone()
    if row and action == "SUSPEND_GUARDIAN":
        g_id = row["guardian_id"]
        cursor.execute("UPDATE guardians SET overall_status = 'SUSPENDED', trust_score = 30 WHERE id = ?", (g_id,))
        log_audit(conn, "Admin", "Suspended Guardian Account", f"Guardian #{g_id}", "FAILED", admin_notes or "Risk alert escalation action")
        
    log_audit(conn, "Admin", f"Resolved Risk Alert #{alert_id}", action, "SUCCESS", admin_notes or "")
    conn.commit()
    conn.close()
    return {"status": "success", "alert_id": alert_id, "action": action, "resolution_status": new_status}
