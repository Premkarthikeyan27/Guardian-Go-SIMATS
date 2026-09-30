import json
from datetime import datetime
from typing import Dict, List, Optional
from backend.database import get_db_connection
from backend.models import dict_from_row, dicts_from_rows

VALID_BOOKING_STATUSES = [
    "REQUESTED", "ACCEPTED", "CONFIRMED", "CHECKED_IN",
    "IN_PROGRESS", "CHECKED_OUT", "COMPLETED", "CANCELLED"
]

def log_audit(conn, actor: str, action: str, resource: str, status: str = "SUCCESS", details: str = ""):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO audit_logs (timestamp, actor, action, resource, status, details) VALUES (?, ?, ?, ?, ?, ?)",
        (now_str, actor, action, resource, status, details)
    )

def list_bookings(role: str = None, user_id: int = None, status_filter: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM bookings"
    params = []
    conditions = []
    
    if role == "parent" and user_id:
        conditions.append("parent_id = ?")
        params.append(user_id)
    elif role == "guardian" and user_id:
        conditions.append("guardian_id = ?")
        params.append(user_id)
        
    if status_filter:
        conditions.append("status = ?")
        params.append(status_filter)
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return dicts_from_rows(rows)

def check_booking_conflict(guardian_id: int, date_str: str, time_str: str) -> bool:
    """Return True if guardian already has an active/confirmed booking for date and time block."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM bookings
        WHERE guardian_id = ? AND date = ? AND time = ?
        AND status IN ('REQUESTED', 'ACCEPTED', 'CONFIRMED', 'CHECKED_IN', 'IN_PROGRESS')
    """, (guardian_id, date_str, time_str))
    conflict = cursor.fetchone()
    conn.close()
    return conflict is not None

def create_booking(parent_id: int, guardian_id: int, parent_name: str, date_str: str, time_str: str, care_type: str, notes: str):
    """Create new booking with conflict validation."""
    if check_booking_conflict(guardian_id, date_str, time_str):
        raise ValueError(f"Schedule Conflict: Guardian #{guardian_id} already has a booking on {date_str} at {time_str}.")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM guardians WHERE id = ?", (guardian_id,))
    g_row = cursor.fetchone()
    guardian_name = g_row["name"] if g_row else f"Guardian #{guardian_id}"
    
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO bookings (parent_id, guardian_id, parent_name, guardian_name, date, time, care_type, notes, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'REQUESTED', ?)
    """, (parent_id, guardian_id, parent_name, guardian_name, date_str, time_str, care_type, notes, now_str))
    
    booking_id = cursor.lastrowid
    log_audit(conn, f"Parent ({parent_name})", "Created Booking Request", f"Booking #{booking_id}", "SUCCESS", f"Care: {care_type} with {guardian_name}")
    conn.commit()
    
    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    row = cursor.fetchone()
    conn.close()
    return dict_from_row(row)

def update_booking_status(booking_id: int, status: str, actor_name: str = "Guardian"):
    """Update booking lifecycle status."""
    status_upper = status.upper()
    if status_upper not in VALID_BOOKING_STATUSES:
        raise ValueError(f"Invalid booking status '{status}'. Must be one of {VALID_BOOKING_STATUSES}")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", (status_upper, booking_id))
    log_audit(conn, actor_name, f"Updated Booking Status to {status_upper}", f"Booking #{booking_id}", "SUCCESS", f"Lifecycle status transition: {status_upper}")
    conn.commit()
    
    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    row = cursor.fetchone()
    conn.close()
    return dict_from_row(row)

def search_guardians(
    query: Optional[str] = None,
    service_type: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_rate: Optional[float] = None
) -> List[Dict]:
    """Search & filter verified guardians."""
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "SELECT * FROM guardians WHERE overall_status = 'VERIFIED'"
    params = []
    
    if query:
        sql += " AND (LOWER(name) LIKE ? OR LOWER(skills) LIKE ? OR LOWER(experience) LIKE ? OR LOWER(bio) LIKE ?)"
        q_wild = f"%{query.lower()}%"
        params.extend([q_wild, q_wild, q_wild, q_wild])
        
    if service_type:
        sql += " AND (LOWER(skills) LIKE ? OR LOWER(bio) LIKE ?)"
        s_wild = f"%{service_type.lower()}%"
        params.extend([s_wild, s_wild])
        
    if min_rating:
        sql += " AND rating >= ?"
        params.append(min_rating)
        
    if max_rate:
        sql += " AND hourly_rate <= ?"
        params.append(max_rate)
        
    sql += " ORDER BY rating DESC, trust_score DESC"
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return dicts_from_rows(rows)

def set_guardian_availability(
    guardian_id: int,
    date_str: str,
    time_slots: List[str],
    service_types: Optional[List[str]] = None,
    specialization: Optional[str] = "Childcare"
) -> Dict:
    """Set or update guardian availability for a date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    slots_json = json.dumps(time_slots)
    services_json = json.dumps(service_types or ["Standard Care", "Pediatric Care"])
    
    cursor.execute("""
        INSERT INTO availability (guardian_id, date, time_slots, service_types, specialization, is_available, updated_at)
        VALUES (?, ?, ?, ?, ?, 1, ?)
        ON CONFLICT(id) DO UPDATE SET
        time_slots = ?, service_types = ?, specialization = ?, is_available = 1, updated_at = ?
    """, (guardian_id, date_str, slots_json, services_json, specialization, now_str, slots_json, services_json, specialization, now_str))
    
    log_audit(conn, f"Guardian #{guardian_id}", "Updated Availability Schedule", f"Date: {date_str}", "SUCCESS", f"Slots: {time_slots}")
    conn.commit()
    conn.close()
    return get_guardian_availability(guardian_id, date_str)

def get_guardian_availability(guardian_id: int, date_str: Optional[str] = None) -> Dict:
    """Fetch availability for a guardian."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if date_str:
        cursor.execute("SELECT * FROM availability WHERE guardian_id = ? AND date = ?", (guardian_id, date_str))
        rows = cursor.fetchall()
    else:
        cursor.execute("SELECT * FROM availability WHERE guardian_id = ? ORDER BY id DESC", (guardian_id,))
        rows = cursor.fetchall()
    conn.close()
    return {"guardian_id": guardian_id, "availability": dicts_from_rows(rows)}

def check_in_session(booking_id: int, guardian_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_time = datetime.now().strftime("%H:%M")
    
    cursor.execute("UPDATE bookings SET status = 'CHECKED_IN' WHERE id = ?", (booking_id,))
    
    cursor.execute("SELECT * FROM care_sessions WHERE booking_id = ?", (booking_id,))
    session = cursor.fetchone()
    
    if session:
        cursor.execute("UPDATE care_sessions SET check_in_time = ?, status = 'IN_PROGRESS' WHERE booking_id = ?", (now_time, booking_id))
        session_id = session["id"]
    else:
        cursor.execute("INSERT INTO care_sessions (booking_id, guardian_id, check_in_time, status) VALUES (?, ?, ?, 'IN_PROGRESS')", (booking_id, guardian_id, now_time))
        session_id = cursor.lastrowid
        
    log_audit(conn, f"Guardian #{guardian_id}", "Check-in Started", f"Care Session #{session_id}", "SUCCESS", f"Checked in at {now_time}")
    conn.commit()
    
    cursor.execute("SELECT * FROM care_sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    return dict_from_row(row)

def check_out_session(booking_id: int, guardian_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_time = datetime.now().strftime("%H:%M")
    
    cursor.execute("UPDATE bookings SET status = 'COMPLETED' WHERE id = ?", (booking_id,))
    cursor.execute("UPDATE care_sessions SET check_out_time = ?, status = 'COMPLETED' WHERE booking_id = ?", (now_time, booking_id))
    
    log_audit(conn, f"Guardian #{guardian_id}", "Check-out Completed", f"Booking #{booking_id}", "SUCCESS", f"Checked out at {now_time}")
    conn.commit()
    
    cursor.execute("SELECT * FROM care_sessions WHERE booking_id = ?", (booking_id,))
    row = cursor.fetchone()
    conn.close()
    return dict_from_row(row)

def add_routine_log(session_id: int, guardian_id: int, category: str, title: str, details: str):
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

def list_routine_logs(guardian_id: int = None, session_id: int = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if session_id:
        cursor.execute("SELECT * FROM care_routines WHERE session_id = ? ORDER BY id DESC", (session_id,))
    elif guardian_id:
        cursor.execute("SELECT * FROM care_routines WHERE guardian_id = ? ORDER BY id DESC", (guardian_id,))
    else:
        cursor.execute("SELECT * FROM care_routines ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return dicts_from_rows(rows)
