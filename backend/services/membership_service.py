from datetime import datetime, timedelta
from typing import Dict, List, Optional
from backend.database import get_db_connection
from backend.models import dict_from_row, dicts_from_rows
from backend.services.booking_service import log_audit

MEMBERSHIP_PLANS = {
    "BASIC_CARE": {
        "id": "BASIC_CARE",
        "name": "Basic Care",
        "monthly_price": "$0 / month",
        "tagline": "Essential caregiver access & safety alerts",
        "features": [
            "Verified Guardian Access",
            "Standard Booking System",
            "Real-time Push Notifications",
            "Service History & Activity Log"
        ],
        "entitlements": {
            "verified_guardians": True,
            "standard_booking": True,
            "notifications": True,
            "service_history": True,
            "certified_caregiver_pref": False,
            "sos_emergency": False,
            "fingerprint_device": False,
            "ble_beacon_device": False,
            "diaper_package": False,
            "nursing_caregivers": False,
            "academic_mentors": False,
            "baby_clothing_kit": False,
            "priority_booking": False,
            "priority_emergency": False,
            "advanced_safety_centre": False
        }
    },
    "SAFECARE": {
        "id": "SAFECARE",
        "name": "SafeCare",
        "monthly_price": "$29 / month",
        "tagline": "Enhanced safety suite with fingerprint device & emergency response",
        "features": [
            "Everything in Basic Care",
            "Certified Caregiver Preference",
            "1-Tap SOS Emergency Response",
            "Fingerprint Scanner Device Included",
            "Baby Diaper Package Delivered",
            "Enhanced Safety Centre Monitoring"
        ],
        "entitlements": {
            "verified_guardians": True,
            "standard_booking": True,
            "notifications": True,
            "service_history": True,
            "certified_caregiver_pref": True,
            "sos_emergency": True,
            "fingerprint_device": True,
            "ble_beacon_device": False,
            "diaper_package": True,
            "nursing_caregivers": False,
            "academic_mentors": False,
            "baby_clothing_kit": False,
            "priority_booking": False,
            "priority_emergency": True,
            "advanced_safety_centre": True
        }
    },
    "PREMIUM_CARE_PLUS": {
        "id": "PREMIUM_CARE_PLUS",
        "name": "Premium Care+",
        "monthly_price": "$79 / month",
        "tagline": "All-inclusive VIP family care with BLE Beacon & specialized nurses",
        "features": [
            "Everything in SafeCare",
            "BLE Beacon Device Included",
            "Fingerprint Scanner Hardware",
            "Professional Nursing Caregivers",
            "Academic & Homework Mentors",
            "Baby Clothing Kit Package",
            "Priority Booking & Concierge Support",
            "Priority Emergency Response Team",
            "Advanced Safety Centre & Live BLE Proximity"
        ],
        "entitlements": {
            "verified_guardians": True,
            "standard_booking": True,
            "notifications": True,
            "service_history": True,
            "certified_caregiver_pref": True,
            "sos_emergency": True,
            "fingerprint_device": True,
            "ble_beacon_device": True,
            "diaper_package": True,
            "nursing_caregivers": True,
            "academic_mentors": True,
            "baby_clothing_kit": True,
            "priority_booking": True,
            "priority_emergency": True,
            "advanced_safety_centre": True
        }
    }
}

def get_membership_plans() -> Dict:
    """Return catalog of exact 3 membership tiers."""
    return {"plans": list(MEMBERSHIP_PLANS.values())}

def get_user_membership(user_id: int) -> Dict:
    """Get active membership for user or default to BASIC_CARE."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM memberships WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        next_year = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
        return {
            "user_id": user_id,
            "plan": "BASIC_CARE",
            "plan_details": MEMBERSHIP_PLANS["BASIC_CARE"],
            "status": "ACTIVE",
            "start_date": now_str,
            "end_date": next_year,
            "renewal_status": "AUTO_RENEW",
            "entitlements": MEMBERSHIP_PLANS["BASIC_CARE"]["entitlements"]
        }
        
    m_dict = dict_from_row(row)
    plan_key = m_dict["plan"]
    plan_info = MEMBERSHIP_PLANS.get(plan_key, MEMBERSHIP_PLANS["BASIC_CARE"])
    
    return {
        "id": m_dict["id"],
        "user_id": m_dict["user_id"],
        "plan": plan_key,
        "plan_details": plan_info,
        "status": m_dict["status"],
        "start_date": m_dict["start_date"],
        "end_date": m_dict["end_date"],
        "renewal_status": m_dict["renewal_status"],
        "entitlements": plan_info["entitlements"]
    }

def subscribe_user(user_id: int, plan: str, payment_info: Optional[Dict] = None) -> Dict:
    """Subscribe or change user membership tier with simulated payment processing."""
    if plan not in MEMBERSHIP_PLANS:
        raise ValueError(f"Invalid plan '{plan}'. Must be one of BASIC_CARE, SAFECARE, PREMIUM_CARE_PLUS.")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    end_str = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
    
    # Process simulated demo payment
    payment_status = "SIMULATED_SUCCESS"
    txn_id = f"PAY-DEMO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    cursor.execute("""
        INSERT INTO memberships (user_id, plan, status, start_date, end_date, renewal_status, created_at, updated_at)
        VALUES (?, ?, 'ACTIVE', ?, ?, 'AUTO_RENEW', ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
        plan = ?, status = 'ACTIVE', start_date = ?, end_date = ?, updated_at = ?
    """, (user_id, plan, now_str, end_str, now_str, now_str, plan, now_str, end_str, now_str))
    
    plan_name = MEMBERSHIP_PLANS[plan]["name"]
    log_audit(conn, f"User #{user_id}", "Subscribed to Membership", plan_name, "SUCCESS", f"Payment Txn: {txn_id} ({payment_status})")
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "message": f"Successfully subscribed to {plan_name}",
        "transaction_id": txn_id,
        "payment_status": payment_status,
        "membership": get_user_membership(user_id)
    }

def upgrade_membership(user_id: int, new_plan: str) -> Dict:
    """Upgrade existing membership to a higher plan."""
    return subscribe_user(user_id, new_plan)

def cancel_membership(user_id: int) -> Dict:
    """Cancel membership renewal and downgrade to Basic Care at period end."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        UPDATE memberships
        SET status = 'CANCELLED', renewal_status = 'MANUAL', updated_at = ?
        WHERE user_id = ?
    """, (now_str, user_id))
    
    log_audit(conn, f"User #{user_id}", "Cancelled Membership", "Membership Plan", "SUCCESS", "Downgraded auto-renewal")
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "message": "Membership auto-renewal cancelled.",
        "membership": get_user_membership(user_id)
    }

def check_entitlement(user_id: int, feature_key: str) -> Dict:
    """Backend security boundary enforcing feature access based on membership plan."""
    m_info = get_user_membership(user_id)
    if m_info["status"] != "ACTIVE":
        return {
            "allowed": False,
            "feature": feature_key,
            "user_id": user_id,
            "reason": "Membership account is inactive or expired",
            "current_plan": m_info["plan"]
        }
        
    entitlements = m_info["entitlements"]
    allowed = entitlements.get(feature_key, False)
    
    return {
        "allowed": allowed,
        "feature": feature_key,
        "user_id": user_id,
        "current_plan": m_info["plan"],
        "reason": f"Access granted for plan '{m_info['plan']}'" if allowed else f"Feature '{feature_key}' requires upgrade from '{m_info['plan']}'"
    }

def list_all_memberships() -> List[Dict]:
    """Admin function to list all registered user memberships."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.*, u.name as user_name, u.email as user_email
        FROM memberships m
        JOIN users u ON m.user_id = u.id
        ORDER BY m.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return dicts_from_rows(rows)
