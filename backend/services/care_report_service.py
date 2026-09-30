import json
from datetime import datetime
from typing import Dict, List, Optional
from backend.database import get_db_connection
from backend.models import dict_from_row, dicts_from_rows
from backend.services.booking_service import log_audit
from backend.services.ai_service import generate_report_ai_summary

def _format_report_row(row) -> Dict:
    if not row:
        return None
    d = dict_from_row(row)
    # Parse JSON strings safely
    for field in ["meals", "naps"]:
        if isinstance(d.get(field), str):
            try:
                d[field] = json.loads(d[field])
            except Exception:
                d[field] = {}
    for field in ["activities", "photos"]:
        if isinstance(d.get(field), str):
            try:
                d[field] = json.loads(d[field])
            except Exception:
                d[field] = []
    return d

async def create_daily_report(
    booking_id: int,
    guardian_id: int,
    child_name: str,
    date: str,
    parent_id: int = 1,
    session_id: Optional[int] = None,
    meals: Optional[Dict] = None,
    naps: Optional[Dict] = None,
    activities: Optional[List[str]] = None,
    mood: str = "Happy & Energetic",
    health_notes: str = "None",
    photos: Optional[List[str]] = None
) -> Dict:
    meals = meals or {}
    naps = naps or {}
    activities = activities or []
    photos = photos or []

    meals_json = json.dumps(meals)
    naps_json = json.dumps(naps)
    activities_json = json.dumps(activities)
    photos_json = json.dumps(photos)

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Generate Local Qwen AI Summary
    ai_res = await generate_report_ai_summary({
        "child_name": child_name,
        "mood": mood,
        "meals": meals,
        "naps": naps,
        "activities": activities,
        "health_notes": health_notes
    })
    ai_summary = ai_res.get("summary", "")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO daily_reports (
            booking_id, session_id, guardian_id, parent_id, child_name, date,
            meals, naps, activities, mood, health_notes, photos, ai_summary, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        booking_id, session_id, guardian_id, parent_id, child_name, date,
        meals_json, naps_json, activities_json, mood, health_notes, photos_json, ai_summary, now_str
    ))

    report_id = cursor.lastrowid
    log_audit(conn, f"Guardian #{guardian_id}", "Created Daily Care Report", f"Daily Report #{report_id}", "SUCCESS", f"Report logged for {child_name} on {date}")
    conn.commit()

    cursor.execute("""
        SELECT r.*, g.name as guardian_name, g.avatar as guardian_avatar
        FROM daily_reports r
        LEFT JOIN guardians g ON r.guardian_id = g.id
        WHERE r.id = ?
    """, (report_id,))
    row = cursor.fetchone()
    conn.close()

    formatted = _format_report_row(row)
    formatted["ai_metadata"] = {
        "source": ai_res.get("source"),
        "model": ai_res.get("model")
    }
    return formatted

def get_daily_reports_for_parent(parent_id: int = 1) -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, g.name as guardian_name, g.avatar as guardian_avatar, g.rating as guardian_rating
        FROM daily_reports r
        LEFT JOIN guardians g ON r.guardian_id = g.id
        WHERE r.parent_id = ?
        ORDER BY r.id DESC
    """, (parent_id,))
    rows = cursor.fetchall()
    conn.close()
    return [_format_report_row(r) for r in rows]

def get_daily_reports_for_guardian(guardian_id: int) -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, g.name as guardian_name, g.avatar as guardian_avatar
        FROM daily_reports r
        LEFT JOIN guardians g ON r.guardian_id = g.id
        WHERE r.guardian_id = ?
        ORDER BY r.id DESC
    """, (guardian_id,))
    rows = cursor.fetchall()
    conn.close()
    return [_format_report_row(r) for r in rows]

def get_daily_report_by_id(report_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, g.name as guardian_name, g.avatar as guardian_avatar, g.rating as guardian_rating
        FROM daily_reports r
        LEFT JOIN guardians g ON r.guardian_id = g.id
        WHERE r.id = ?
    """, (report_id,))
    row = cursor.fetchone()
    conn.close()
    return _format_report_row(row)

async def refresh_report_ai_summary(report_id: int) -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM daily_reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"error": "Report not found"}

    rep = _format_report_row(row)
    ai_res = await generate_report_ai_summary(rep)
    new_summary = ai_res.get("summary", "")

    cursor.execute("UPDATE daily_reports SET ai_summary = ? WHERE id = ?", (new_summary, report_id))
    log_audit(conn, "AI Engine", "Refreshed Report AI Summary", f"Daily Report #{report_id}", "SUCCESS", "Local Qwen AI summary regenerated")
    conn.commit()
    conn.close()

    rep["ai_summary"] = new_summary
    rep["ai_metadata"] = {
        "source": ai_res.get("source"),
        "model": ai_res.get("model")
    }
    return rep
