from datetime import datetime
from typing import Dict, List, Optional
from backend.database import get_db_connection
from backend.models import dict_from_row, dicts_from_rows
from backend.services.booking_service import log_audit
from backend.services.notification_service import send_notification

def add_family_member(
    parent_id: int,
    name: str,
    email: str,
    relation: str,
    access_level: str = "CARE_VIEWER"
) -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO family_members (parent_id, name, email, relation, access_level, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'ACTIVE', ?)
    """, (parent_id, name, email, relation, access_level, now_str))

    member_id = cursor.lastrowid
    log_audit(conn, f"Parent #{parent_id}", "Invited Family Circle Member", f"Family Member #{member_id}", "SUCCESS", f"Added {name} ({relation}) with {access_level} access.")
    conn.commit()

    # Dispatch invite notification
    send_notification(
        user_id=parent_id,
        type="FAMILY_CIRCLE",
        title="Family Circle Updated",
        message=f"{name} ({relation}) has been added to your Family Circle.",
        channel="PUSH"
    )

    cursor.execute("SELECT * FROM family_members WHERE id = ?", (member_id,))
    row = cursor.fetchone()
    conn.close()
    return dict_from_row(row)

def get_family_members(parent_id: int = 1) -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM family_members WHERE parent_id = ? AND status = 'ACTIVE' ORDER BY id DESC", (parent_id,))
    rows = cursor.fetchall()
    conn.close()
    return dicts_from_rows(rows)

def remove_family_member(member_id: int, parent_id: int = 1) -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE family_members SET status = 'REMOVED' WHERE id = ? AND parent_id = ?", (member_id, parent_id))
    log_audit(conn, f"Parent #{parent_id}", "Removed Family Member", f"Family Member #{member_id}", "SUCCESS", "Family circle access revoked.")
    conn.commit()
    conn.close()
    return {
        "member_id": member_id,
        "parent_id": parent_id,
        "status": "REMOVED"
    }

def add_care_routine(
    guardian_id: int,
    category: str,
    title: str,
    details: str = "",
    session_id: Optional[int] = 1
) -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO care_routines (session_id, guardian_id, category, title, details, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, guardian_id, category, title, details, now_str))

    routine_id = cursor.lastrowid
    log_audit(conn, f"Guardian #{guardian_id}", "Logged Care Routine", f"Routine #{routine_id}", "SUCCESS", f"{category.upper()}: {title}")
    conn.commit()

    cursor.execute("SELECT * FROM care_routines WHERE id = ?", (routine_id,))
    row = cursor.fetchone()
    conn.close()
    return dict_from_row(row)

def get_session_care_routines(session_id: int = 1) -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM care_routines WHERE session_id = ? ORDER BY id DESC", (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return dicts_from_rows(rows)

def get_guardian_care_routines(guardian_id: int) -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM care_routines WHERE guardian_id = ? ORDER BY id DESC", (guardian_id,))
    rows = cursor.fetchall()
    conn.close()
    return dicts_from_rows(rows)
