import sqlite3
import os
from datetime import datetime

from backend.services.auth_service import hash_password

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "guardian_go.db")

_db_initialized = False

def get_db_connection():
    global _db_initialized
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    if not _db_initialized:
        _db_initialized = True
        init_db()
        seed_db()
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        phone TEXT,
        avatar TEXT,
        password_hash TEXT
    );

    CREATE TABLE IF NOT EXISTS dependents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        special_needs TEXT DEFAULT 'None',
        allergies TEXT DEFAULT 'None',
        instructions TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(parent_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS guardians (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        avatar TEXT,
        rating REAL DEFAULT 4.9,
        experience TEXT,
        skills TEXT,
        cpr_status TEXT DEFAULT 'VERIFIED',
        bg_status TEXT DEFAULT 'VERIFIED',
        identity_status TEXT DEFAULT 'VERIFIED',
        doc_status TEXT DEFAULT 'VERIFIED',
        training_status TEXT DEFAULT 'COMPLETED',
        overall_status TEXT DEFAULT 'VERIFIED',
        trust_score INTEGER DEFAULT 96,
        hourly_rate REAL DEFAULT 28.0,
        distance TEXT DEFAULT '1.2 km',
        availability TEXT DEFAULT 'Available Today',
        bio TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_id INTEGER NOT NULL,
        guardian_id INTEGER NOT NULL,
        parent_name TEXT,
        guardian_name TEXT,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        care_type TEXT NOT NULL,
        notes TEXT,
        status TEXT NOT NULL DEFAULT 'REQUESTED',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS availability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guardian_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        time_slots TEXT NOT NULL DEFAULT '["09:00 - 13:00", "14:00 - 18:00"]',
        service_types TEXT DEFAULT '["Standard Care", "Pediatric Care"]',
        specialization TEXT DEFAULT 'Childcare',
        is_available INTEGER DEFAULT 1,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(guardian_id) REFERENCES guardians(id)
    );

    CREATE TABLE IF NOT EXISTS care_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL,
        guardian_id INTEGER NOT NULL,
        check_in_time TEXT,
        check_out_time TEXT,
        status TEXT NOT NULL DEFAULT 'IN_PROGRESS'
    );

    CREATE TABLE IF NOT EXISTS care_routines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        guardian_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        details TEXT,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS verification_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guardian_id INTEGER NOT NULL,
        document_type TEXT NOT NULL,
        document_url TEXT,
        status TEXT NOT NULL DEFAULT 'VERIFIED',
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS safety_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        guardian_id INTEGER,
        event_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS beacons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_name TEXT NOT NULL,
        mac_address TEXT NOT NULL,
        connected INTEGER DEFAULT 1,
        rssi INTEGER DEFAULT -52,
        distance_m REAL DEFAULT 3.4,
        battery_pct INTEGER DEFAULT 92,
        safe_zone_active INTEGER DEFAULT 1,
        in_safe_zone INTEGER DEFAULT 1,
        last_seen TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS guardian_passports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guardian_id INTEGER UNIQUE NOT NULL,
        trust_score INTEGER DEFAULT 96,
        completed_bookings INTEGER DEFAULT 42,
        cancellation_rate REAL DEFAULT 0.0,
        rating REAL DEFAULT 4.9,
        identity_verified INTEGER DEFAULT 1,
        qualification_verified INTEGER DEFAULT 1,
        police_status TEXT DEFAULT 'VERIFIED',
        address_status TEXT DEFAULT 'VERIFIED',
        face_verified INTEGER DEFAULT 1,
        liveness_passed INTEGER DEFAULT 1,
        expiry_date TEXT NOT NULL,
        badges TEXT DEFAULT '["CPR Certified", "Pediatric Care", "Police Cleared", "Background Checked"]',
        updated_at TEXT NOT NULL,
        FOREIGN KEY(guardian_id) REFERENCES guardians(id)
    );

    CREATE TABLE IF NOT EXISTS risk_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guardian_id INTEGER NOT NULL,
        alert_type TEXT NOT NULL,
        severity TEXT NOT NULL DEFAULT 'MEDIUM',
        description TEXT NOT NULL,
        ai_confidence REAL DEFAULT 0.85,
        explainable_signals TEXT DEFAULT '[]',
        status TEXT NOT NULL DEFAULT 'OPEN',
        admin_notes TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(guardian_id) REFERENCES guardians(id)
    );

    CREATE TABLE IF NOT EXISTS digilocker_verifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guardian_id INTEGER UNIQUE NOT NULL,
        status TEXT NOT NULL DEFAULT 'NOT_STARTED',
        txn_id TEXT,
        aadhaar_last_four TEXT DEFAULT 'XXXX',
        verified_name TEXT,
        documents_found TEXT DEFAULT '[]',
        mode TEXT NOT NULL DEFAULT 'DEMO_VERIFIED',
        consent_timestamp TEXT,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(guardian_id) REFERENCES guardians(id)
    );

    CREATE TABLE IF NOT EXISTS memberships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        plan TEXT NOT NULL DEFAULT 'BASIC_CARE',
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        renewal_status TEXT NOT NULL DEFAULT 'AUTO_RENEW',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS daily_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL,
        session_id INTEGER,
        guardian_id INTEGER NOT NULL,
        parent_id INTEGER NOT NULL,
        child_name TEXT NOT NULL,
        date TEXT NOT NULL,
        meals TEXT DEFAULT '{}',
        naps TEXT DEFAULT '{}',
        activities TEXT DEFAULT '[]',
        mood TEXT DEFAULT 'Happy',
        health_notes TEXT DEFAULT 'None',
        photos TEXT DEFAULT '[]',
        ai_summary TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        FOREIGN KEY(booking_id) REFERENCES bookings(id),
        FOREIGN KEY(guardian_id) REFERENCES guardians(id),
        FOREIGN KEY(parent_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        channel TEXT NOT NULL DEFAULT 'PUSH',
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS family_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        relation TEXT NOT NULL,
        access_level TEXT NOT NULL DEFAULT 'CARE_VIEWER',
        status TEXT DEFAULT 'ACTIVE',
        created_at TEXT NOT NULL,
        FOREIGN KEY(parent_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_id INTEGER NOT NULL,
        guardian_id INTEGER NOT NULL,
        booking_id INTEGER,
        complaint_text TEXT NOT NULL,
        sentiment TEXT DEFAULT 'NEGATIVE',
        risk_level TEXT DEFAULT 'MEDIUM',
        category TEXT DEFAULT 'CARE_QUALITY',
        xai_factors TEXT DEFAULT '[]',
        recommended_action TEXT DEFAULT 'INVESTIGATE',
        status TEXT DEFAULT 'OPEN',
        admin_notes TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(parent_id) REFERENCES users(id),
        FOREIGN KEY(guardian_id) REFERENCES guardians(id)
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        actor TEXT NOT NULL,
        action TEXT NOT NULL,
        resource TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'SUCCESS',
        details TEXT
    );
    """)

    # Schema Migration Check: ensure password_hash column exists on existing users table
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [col[1] for col in cursor.fetchall()]
    if "password_hash" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        default_pwd_hash = hash_password("password123")
        cursor.execute("UPDATE users SET password_hash = ?", (default_pwd_hash,))

    conn.commit()
    conn.close()

def seed_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Check if dependents exist
    cursor.execute("SELECT COUNT(*) FROM dependents")
    dep_count = cursor.fetchone()[0]
    if dep_count == 0:
        dependents_data = [
            (1, "Leo Jenkins", 5, "None", "Peanuts", "Takes afternoon snack at 3 PM and reading time before nap", now_str, now_str)
        ]
        cursor.executemany("""
            INSERT INTO dependents (parent_id, name, age, special_needs, allergies, instructions, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, dependents_data)
        conn.commit()

    # Check if users exist
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        # 1. Seed Users
        default_pwd_hash = hash_password("password123")
        users_data = [
            ("Sarah Jenkins", "parent@demo.com", "parent", "+1 555-0192", "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&auto=format&fit=crop&q=80", default_pwd_hash),
            ("Ananya Sharma", "guardian@demo.com", "guardian", "+1 555-0143", "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80", default_pwd_hash),
            ("Priya Patel", "guardian2@demo.com", "guardian", "+1 555-0188", "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&auto=format&fit=crop&q=80", default_pwd_hash),
            ("David Miller", "guardian3@demo.com", "guardian", "+1 555-0167", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80", default_pwd_hash),
            ("System Admin", "admin@demo.com", "admin", "+1 555-0100", "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&auto=format&fit=crop&q=80", default_pwd_hash)
        ]
        cursor.executemany("INSERT INTO users (name, email, role, phone, avatar, password_hash) VALUES (?, ?, ?, ?, ?, ?)", users_data)

        # 1b. Seed Dependents
        dependents_data = [
            (1, "Leo Jenkins", 5, "None", "Peanuts", "Takes afternoon snack at 3 PM and reading time before nap", now_str, now_str)
        ]
        cursor.executemany("""
            INSERT INTO dependents (parent_id, name, age, special_needs, allergies, instructions, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, dependents_data)

        # 2. Seed Guardians
        guardians_data = [
            (2, "Ananya Sharma", "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80", 4.9, "5 years experience", "First Aid, CPR, Special Needs Care, Early Childhood Education", "VERIFIED", "VERIFIED", "VERIFIED", "VERIFIED", "COMPLETED", "VERIFIED", 96, 28.0, "1.2 km", "Available Today", "Certified pediatric care provider with 5+ years of early childhood experience."),
            (3, "Priya Patel", "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&auto=format&fit=crop&q=80", 4.8, "3 years experience", "CPR Certified, Toddler Care, Creative Arts", "VERIFIED", "PENDING", "VERIFIED", "VERIFIED", "COMPLETED", "PENDING", 88, 24.0, "2.5 km", "Available Tomorrow", "Dedicated caregiver specializing in preschool activity planning and safety."),
            (4, "David Miller", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80", 5.0, "6 years experience", "First Aid + CPR, Youth Sports Coach, Emergency Response", "VERIFIED", "VERIFIED", "VERIFIED", "VERIFIED", "COMPLETED", "VERIFIED", 98, 30.0, "0.8 km", "Available Today", "Former EMT and certified child safety specialist with emergency response training.")
        ]
        cursor.executemany("""
            INSERT INTO guardians (user_id, name, avatar, rating, experience, skills, cpr_status, bg_status, identity_status, doc_status, training_status, overall_status, trust_score, hourly_rate, distance, availability, bio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, guardians_data)

        # 3. Seed Bookings
        bookings_data = [
            (1, 1, "Sarah Jenkins", "Ananya Sharma", "Today", "14:00 - 18:00", "Afternoon Childcare", "Please ensure Leo takes his afternoon snack at 3 PM.", "ACCEPTED", now_str),
            (1, 3, "Sarah Jenkins", "David Miller", "Yesterday", "09:00 - 13:00", "Morning Activity & Care", "Park visit and reading time.", "COMPLETED", now_str),
            (1, 2, "Sarah Jenkins", "Priya Patel", "Tomorrow", "10:00 - 14:00", "Infant & Toddler Care", "Routine supervision.", "REQUESTED", now_str)
        ]
        cursor.executemany("""
            INSERT INTO bookings (parent_id, guardian_id, parent_name, guardian_name, date, time, care_type, notes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, bookings_data)

        # 4. Seed Active Care Session
        cursor.execute("""
            INSERT INTO care_sessions (booking_id, guardian_id, check_in_time, status)
            VALUES (1, 1, '14:02', 'IN_PROGRESS')
        """)

        # 5. Seed Care Routines
        routines_data = [
            (1, 1, "meal", "Healthy Afternoon Snack", "Served sliced apples, whole wheat toast, and fresh water. All finished!", now_str),
            (1, 1, "activity", "Educational Puzzle & Reading", "Completed 50-piece animal puzzle and read two storybooks.", now_str),
            (1, 1, "medication", "Multivitamin Administered", "Given 1 chewable pediatric vitamin with water per parent notes.", now_str)
        ]
        cursor.executemany("""
            INSERT INTO care_routines (session_id, guardian_id, category, title, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, routines_data)

        # 6. Seed Verifications
        verifications_data = [
            (1, "Govt Identity Card (Aadhaar / Passport)", "https://example.com/docs/id_ananya.pdf", "VERIFIED", now_str),
            (1, "Criminal Background Check", "https://example.com/docs/bg_ananya.pdf", "VERIFIED", now_str),
            (1, "First Aid & CPR Certification", "https://example.com/docs/cpr_ananya.pdf", "VERIFIED", now_str),
            (2, "Govt Identity Card (Aadhaar / Passport)", "https://example.com/docs/id_priya.pdf", "VERIFIED", now_str),
            (2, "Criminal Background Check", "https://example.com/docs/bg_priya.pdf", "PENDING", now_str),
            (3, "Govt Identity Card (Aadhaar / Passport)", "https://example.com/docs/id_david.pdf", "VERIFIED", now_str),
            (3, "Criminal Background Check", "https://example.com/docs/bg_david.pdf", "VERIFIED", now_str)
        ]
        cursor.executemany("""
            INSERT INTO verification_records (guardian_id, document_type, document_url, status, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, verifications_data)

        # 6c. Seed DigiLocker Verifications
        digilocker_data = [
            (1, "DEMO_VERIFIED", "TXN-DL-1001", "8842", "Ananya Sharma", '["Aadhaar Card", "Class XII Marksheet", "Degree Certificate"]', "DEMO_VERIFIED", now_str, now_str),
            (2, "PENDING_CONSENT", "TXN-DL-1002", "3319", "Priya Patel", '["Aadhaar Card"]', "DEMO_VERIFIED", now_str, now_str),
            (3, "VERIFIED", "TXN-DL-1003", "5501", "David Miller", '["Aadhaar Card", "EMT License", "CPR Certificate"]', "DEMO_VERIFIED", now_str, now_str)
        ]
        cursor.executemany("""
            INSERT INTO digilocker_verifications (guardian_id, status, txn_id, aadhaar_last_four, verified_name, documents_found, mode, consent_timestamp, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, digilocker_data)

        # 6d. Seed Memberships
        next_year_str = "2027-12-31 23:59:59"
        memberships_data = [
            (1, "PREMIUM_CARE_PLUS", "ACTIVE", now_str, next_year_str, "AUTO_RENEW", now_str, now_str)
        ]
        cursor.executemany("""
            INSERT INTO memberships (user_id, plan, status, start_date, end_date, renewal_status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, memberships_data)

        # 6e. Seed Guardian Availability
        availability_data = [
            (1, "Today", '["14:00 - 18:00", "18:30 - 21:00"]', '["Standard Care", "Pediatric Care", "Infant Care"]', "Childcare & Early Childhood", 1, now_str),
            (2, "Tomorrow", '["09:00 - 13:00", "14:00 - 17:00"]', '["Toddler Care", "Creative Arts"]', "Preschool Activity", 1, now_str),
            (3, "Today", '["09:00 - 13:00", "14:00 - 18:00"]', '["Emergency Response", "Youth Sports", "Nursing Caregiver"]', "Child Safety Specialist", 1, now_str)
        ]
        cursor.executemany("""
            INSERT INTO availability (guardian_id, date, time_slots, service_types, specialization, is_available, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, availability_data)

        # 6f. Seed Risk Alerts
        risk_alerts_data = [
            (2, "VERIFICATION_FAILURE", "MEDIUM", "Background check document pending verification for >14 days", 0.88, '["Pending Criminal Audit", "Expired First Aid Refresh"]', "OPEN", "Pending admin verification decision", now_str, now_str)
        ]
        cursor.executemany("""
            INSERT INTO risk_alerts (guardian_id, alert_type, severity, description, ai_confidence, explainable_signals, status, admin_notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, risk_alerts_data)

        # 7. Seed Beacon
        cursor.execute("""
            INSERT INTO beacons (child_name, mac_address, connected, rssi, distance_m, battery_pct, safe_zone_active, in_safe_zone, last_seen)
            VALUES ('Leo Jenkins', 'C4:7F:51:8B:2A:09', 1, -52, 3.4, 92, 1, 1, ?)
        """, (now_str,))

        # 8. Seed Initial Safety Events
        safety_events_data = [
            (1, 1, "LATE_CHECKIN", "WARNING", "Guardian check-in delayed by 2 minutes (resolved automatically).", "RESOLVED", now_str)
        ]
        cursor.executemany("""
            INSERT INTO safety_events (user_id, guardian_id, event_type, severity, description, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, safety_events_data)

        # 8b. Seed Daily Care Reports
        daily_reports_data = [
            (
                2, 1, 3, 1, "Leo Jenkins", "Yesterday",
                '{"breakfast": "Oatmeal with berries", "lunch": "Grilled chicken & veggies", "snacks": "Sliced apples & almond butter", "water_intake": "650 ml"}',
                '{"start": "13:15", "end": "14:30", "duration_mins": 75, "quality": "Restful"}',
                '["Completed 50-piece animal puzzle", "Outdoor park walk & swing play", "Reading storybooks"]',
                "Happy & Energetic",
                "Leo was in great spirits. Applied sunscreen before park trip.",
                '["https://images.unsplash.com/photo-1502086223501-7ea6ecd79368?w=300&auto=format&fit=crop&q=80"]',
                "AI Breakdown: Leo had a balanced daily routine with healthy nutrition and 75 minutes of restorative sleep. High engagement during cognitive puzzle play.",
                now_str
            )
        ]
        cursor.executemany("""
            INSERT INTO daily_reports (booking_id, session_id, guardian_id, parent_id, child_name, date, meals, naps, activities, mood, health_notes, photos, ai_summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, daily_reports_data)

    # Check if notifications exist
    cursor.execute("SELECT COUNT(*) FROM notifications")
    notif_count = cursor.fetchone()[0]
    if notif_count == 0:
        notifications_data = [
            (1, "BOOKING_ACCEPTED", "PUSH", "Booking Confirmed", "Ananya Sharma has accepted your care booking for today at 14:00.", 0, now_str),
            (1, "CHECK_IN", "PUSH", "Caregiver Checked In", "Ananya Sharma checked in at 14:02. Biometric and BLE proximity verified.", 0, now_str),
            (1, "BEACON_STATUS", "PUSH", "BLE Beacon Connected", "Leo's BLE Beacon is active and connected within 3.4 meters.", 1, now_str),
            (2, "BOOKING_REQUESTED", "SMS", "New Care Request", "You have a new booking request from Sarah Jenkins for today.", 0, now_str),
            (5, "RISK_ALERT", "BROADCAST", "Risk Alert Triggered", "Pending background check audit on Guardian #2.", 0, now_str)
        ]
        cursor.executemany("""
            INSERT INTO notifications (user_id, type, channel, title, message, is_read, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, notifications_data)
        conn.commit()

    # Check if family_members exist
    cursor.execute("SELECT COUNT(*) FROM family_members")
    fm_count = cursor.fetchone()[0]
    if fm_count == 0:
        family_data = [
            (1, "Robert Jenkins", "grandpa@demo.com", "Grandparent", "FULL_ACCESS", "ACTIVE", now_str),
            (1, "Emily Jenkins", "emily@demo.com", "Co-Parent / Aunt", "CARE_VIEWER", "ACTIVE", now_str)
        ]
        cursor.executemany("""
            INSERT INTO family_members (parent_id, name, email, relation, access_level, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, family_data)
        conn.commit()

    # Check if complaints exist
    cursor.execute("SELECT COUNT(*) FROM complaints")
    comp_count = cursor.fetchone()[0]
    if comp_count == 0:
        complaints_data = [
            (
                1, 2, 3,
                "Caregiver arrived 15 minutes late without prior notice and forgot to log afternoon meal routine.",
                "NEGATIVE", "MEDIUM", "TARDINESS",
                '["15-minute tardiness without notification", "Incomplete meal routine log", "Minor care policy departure"]',
                "WARN_GUARDIAN", "OPEN", "Pending admin review", now_str
            )
        ]
        cursor.executemany("""
            INSERT INTO complaints (parent_id, guardian_id, booking_id, complaint_text, sentiment, risk_level, category, xai_factors, recommended_action, status, admin_notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, complaints_data)
        conn.commit()

    conn.close()
