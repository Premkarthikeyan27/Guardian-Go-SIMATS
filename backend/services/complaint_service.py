import json
from datetime import datetime
from typing import Dict, List, Optional
from backend.database import get_db_connection
from backend.models import dict_from_row, dicts_from_rows
from backend.services.booking_service import log_audit
from backend.services.ai_service import analyze_complaint_nlp

def _format_complaint_row(row) -> Dict:
    if not row:
        return None
    d = dict_from_row(row)
    if isinstance(d.get("xai_factors"), str):
        try:
            d["xai_factors"] = json.loads(d["xai_factors"])
        except Exception:
            d["xai_factors"] = []
    return d

async def submit_complaint(
    parent_id: int,
    guardian_id: int,
    complaint_text: str,
    booking_id: Optional[int] = None
) -> Dict:
    nlp_res = await analyze_complaint_nlp(complaint_text)

    sentiment = nlp_res.get("sentiment", "NEGATIVE")
    risk_level = nlp_res.get("risk_level", "MEDIUM")
    category = nlp_res.get("category", "CARE_QUALITY")
    xai_factors = nlp_res.get("xai_factors", [])
    recommended_action = nlp_res.get("recommended_action", "INVESTIGATE")

    xai_factors_json = json.dumps(xai_factors)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO complaints (
            parent_id, guardian_id, booking_id, complaint_text, sentiment,
            risk_level, category, xai_factors, recommended_action, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
    """, (
        parent_id, guardian_id, booking_id, complaint_text, sentiment,
        risk_level, category, xai_factors_json, recommended_action, now_str
    ))

    complaint_id = cursor.lastrowid
    log_audit(conn, f"Parent #{parent_id}", "Submitted Complaint (NLP Processed)", f"Complaint #{complaint_id}", "SUCCESS", f"Risk: {risk_level} | Category: {category}")

    # If HIGH or CRITICAL risk, auto-create a Risk Alert for Admin Command Center
    if risk_level in ["HIGH", "CRITICAL"]:
        cursor.execute("""
            INSERT INTO risk_alerts (guardian_id, alert_type, severity, description, ai_confidence, explainable_signals, status, created_at, updated_at)
            VALUES (?, 'COMPLAINT_FLAG', ?, ?, 0.92, ?, 'OPEN', ?, ?)
        """, (
            guardian_id,
            "HIGH" if risk_level == "HIGH" else "CRITICAL",
            f"NLP Risk Flag from Parent Complaint #{complaint_id}: {complaint_text[:100]}",
            xai_factors_json,
            now_str,
            now_str
        ))

    conn.commit()

    cursor.execute("""
        SELECT c.*, u.name as parent_name, g.name as guardian_name, g.avatar as guardian_avatar
        FROM complaints c
        LEFT JOIN users u ON c.parent_id = u.id
        LEFT JOIN guardians g ON c.guardian_id = g.id
        WHERE c.id = ?
    """, (complaint_id,))
    row = cursor.fetchone()
    conn.close()

    formatted = _format_complaint_row(row)
    formatted["nlp_metadata"] = {
        "source": nlp_res.get("source"),
        "model": nlp_res.get("model")
    }
    return formatted

def get_all_complaints(status: Optional[str] = None, risk_level: Optional[str] = None) -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT c.*, u.name as parent_name, g.name as guardian_name, g.avatar as guardian_avatar
        FROM complaints c
        LEFT JOIN users u ON c.parent_id = u.id
        LEFT JOIN guardians g ON c.guardian_id = g.id
        WHERE 1=1
    """
    params = []
    if status:
        query += " AND c.status = ?"
        params.append(status)
    if risk_level:
        query += " AND c.risk_level = ?"
        params.append(risk_level)
    query += " ORDER BY c.id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [_format_complaint_row(r) for r in rows]

def get_parent_complaints(parent_id: int) -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, g.name as guardian_name, g.avatar as guardian_avatar
        FROM complaints c
        LEFT JOIN guardians g ON c.guardian_id = g.id
        WHERE c.parent_id = ?
        ORDER BY c.id DESC
    """, (parent_id,))
    rows = cursor.fetchall()
    conn.close()
    return [_format_complaint_row(r) for r in rows]

def get_guardian_complaints(guardian_id: int) -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, u.name as parent_name
        FROM complaints c
        LEFT JOIN users u ON c.parent_id = u.id
        WHERE c.guardian_id = ?
        ORDER BY c.id DESC
    """, (guardian_id,))
    rows = cursor.fetchall()
    conn.close()
    return [_format_complaint_row(r) for r in rows]

def resolve_complaint(
    complaint_id: int,
    action: str,
    admin_notes: str = None,
    actor_name: str = "Admin Officer"
) -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()

    status = "RESOLVED" if action in ["DISMISS", "WARN_GUARDIAN"] else "ACTIONED"
    notes_str = f"Action taken: {action}."
    if admin_notes:
        notes_str += f" Notes: {admin_notes}"

    cursor.execute("""
        UPDATE complaints
        SET status = ?, recommended_action = ?, admin_notes = ?
        WHERE id = ?
    """, (status, action, notes_str, complaint_id))

    log_audit(conn, actor_name, f"Resolved Complaint #{complaint_id}", f"Action: {action}", "SUCCESS", notes_str)

    # If action is SUSPEND_GUARDIAN, flag guardian status
    if action == "SUSPEND_GUARDIAN":
        cursor.execute("SELECT guardian_id FROM complaints WHERE id = ?", (complaint_id,))
        row = cursor.fetchone()
        if row:
            g_id = row["guardian_id"]
            cursor.execute("UPDATE guardians SET overall_status = 'SUSPENDED' WHERE id = ?", (g_id,))
            log_audit(conn, actor_name, f"Suspended Guardian #{g_id}", "Guardian Status -> SUSPENDED", "WARNING", f"Suspended following complaint #{complaint_id}")

    conn.commit()

    cursor.execute("""
        SELECT c.*, u.name as parent_name, g.name as guardian_name
        FROM complaints c
        LEFT JOIN users u ON c.parent_id = u.id
        LEFT JOIN guardians g ON c.guardian_id = g.id
        WHERE c.id = ?
    """, (complaint_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"error": "Complaint not found"}
    return _format_complaint_row(row)
