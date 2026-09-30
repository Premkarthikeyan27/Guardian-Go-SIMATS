from datetime import datetime
from backend.database import get_db_connection
from backend.models import dict_from_row
from backend.services.booking_service import log_audit

def get_beacon_status(beacon_id: int = 1):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM beacons WHERE id = ?", (beacon_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {
            "id": 1,
            "child_name": "Leo Jenkins",
            "mac_address": "C4:7F:51:8B:2A:09",
            "connected": 1,
            "rssi": -52,
            "distance_m": 3.4,
            "battery_pct": 92,
            "safe_zone_active": 1,
            "in_safe_zone": 1,
            "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    return dict_from_row(row)

def simulate_beacon(action: str, distance_m: float = None, rssi: int = None, beacon_id: int = 1):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if action in ["breach", "warning"]:
        dist = distance_m if distance_m is not None else (18.5 if action == "breach" else 14.2)
        sig = rssi if rssi is not None else (-88 if action == "breach" else -78)
        
        cursor.execute("""
            UPDATE beacons 
            SET distance_m = ?, rssi = ?, in_safe_zone = 0, last_seen = ?
            WHERE id = ?
        """, (dist, sig, now_str, beacon_id))
        
        # Create Safety Event for Safe Zone Breach
        cursor.execute("""
            INSERT INTO safety_events (user_id, guardian_id, event_type, severity, description, status, created_at)
            VALUES (1, 1, 'BEACON_BREACH', 'WARNING', ?, 'ACTIVE', ?)
        """, (f"⚠ BLE Beacon Safe Zone Breach detected! Child is {dist}m away from caregiver (Safe limit: 10m).", now_str))
        
        log_audit(conn, "BLE Simulation Engine", "Safe Zone Breach Triggered", f"Beacon #{beacon_id}", "WARNING", f"Child moved outside perimeter: {dist}m")
        
    elif action == "reset":
        cursor.execute("""
            UPDATE beacons 
            SET distance_m = 3.4, rssi = -52, connected = 1, in_safe_zone = 1, last_seen = ?
            WHERE id = ?
        """, (now_str, beacon_id))
        
        log_audit(conn, "BLE Simulation Engine", "Reset Beacon Safety Zone", f"Beacon #{beacon_id}", "SUCCESS", "Perimeter security restored to 3.4m")
        
    elif action == "connect":
        cursor.execute("""
            UPDATE beacons 
            SET connected = 1, last_seen = ?
            WHERE id = ?
        """, (now_str, beacon_id))
        
        log_audit(conn, "BLE Simulation Engine", "Beacon Connected", f"Beacon #{beacon_id}", "SUCCESS", "Bluetooth Smart Handshake established")
        
    elif action == "disconnect":
        cursor.execute("""
            UPDATE beacons 
            SET connected = 0, last_seen = ?
            WHERE id = ?
        """, (now_str, beacon_id))
        
        log_audit(conn, "BLE Simulation Engine", "Beacon Disconnected", f"Beacon #{beacon_id}", "WARNING", "Signal lost")

    conn.commit()
    
    cursor.execute("SELECT * FROM beacons WHERE id = ?", (beacon_id,))
    row = cursor.fetchone()
    conn.close()
    return dict_from_row(row)
