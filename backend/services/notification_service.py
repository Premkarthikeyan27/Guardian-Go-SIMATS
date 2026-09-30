from datetime import datetime
from typing import Dict, List, Optional
from backend.database import get_db_connection
from backend.models import dict_from_row, dicts_from_rows
from backend.services.booking_service import log_audit

def send_notification(
    user_id: int,
    type: str,
    title: str,
    message: str,
    channel: str = "PUSH"
) -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO notifications (user_id, type, channel, title, message, is_read, created_at)
        VALUES (?, ?, ?, ?, ?, 0, ?)
    """, (user_id, type, channel, title, message, now_str))

    notif_id = cursor.lastrowid
    log_audit(conn, "Notification System", f"Dispatched Notification ({channel})", f"Notification #{notif_id}", "SUCCESS", f"Sent '{title}' to User #{user_id}")
    conn.commit()

    cursor.execute("SELECT * FROM notifications WHERE id = ?", (notif_id,))
    row = cursor.fetchone()
    conn.close()
    return dict_from_row(row)

def get_user_notifications(user_id: int) -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    notifications = dicts_from_rows(rows)

    cursor.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0", (user_id,))
    unread_count = cursor.fetchone()[0]

    conn.close()
    return {
        "user_id": user_id,
        "unread_count": unread_count,
        "notifications": notifications
    }

def mark_notification_as_read(notification_id: int) -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
    conn.commit()

    cursor.execute("SELECT * FROM notifications WHERE id = ?", (notification_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"error": "Notification not found"}
    return dict_from_row(row)

def mark_all_notifications_as_read(user_id: int) -> Dict:
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
    updated_rows = cursor.rowcount
    conn.commit()
    conn.close()

    return {
        "user_id": user_id,
        "status": "ALL_READ",
        "updated_count": updated_rows
    }
