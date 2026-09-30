from fastapi import APIRouter, HTTPException, Query
from backend.services.membership_service import (
    get_membership_plans,
    get_user_membership,
    subscribe_user,
    upgrade_membership,
    cancel_membership,
    check_entitlement,
    list_all_memberships
)
from backend.schemas import (
    MembershipSubscribeRequest,
    MembershipUpgradeRequest,
    MembershipCancelRequest
)

router = APIRouter(tags=["membership"])

@router.get("/api/v1/membership")
def fetch_user_membership(user_id: int = 1):
    """Get active membership & entitlements for specified user."""
    return get_user_membership(user_id)

@router.get("/api/v1/membership/plans")
def fetch_membership_plans():
    """Catalog of exact 3 membership plans (Basic Care, SafeCare, Premium Care+)."""
    return get_membership_plans()

@router.post("/api/v1/membership/subscribe")
def handle_subscribe(req: MembershipSubscribeRequest):
    """Subscribe to plan with simulated payment processing."""
    try:
        return subscribe_user(req.user_id or 1, req.plan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/api/v1/membership/upgrade")
def handle_upgrade(req: MembershipUpgradeRequest):
    """Upgrade membership tier."""
    try:
        return upgrade_membership(req.user_id or 1, req.new_plan)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/api/v1/membership/cancel")
def handle_cancel(req: MembershipCancelRequest):
    """Cancel membership auto-renewal."""
    return cancel_membership(req.user_id or 1)

@router.get("/api/v1/membership/features")
def fetch_features(user_id: int = 1):
    """Fetch feature entitlements for current user."""
    m_info = get_user_membership(user_id)
    return {
        "user_id": user_id,
        "plan": m_info["plan"],
        "entitlements": m_info["entitlements"]
    }

@router.get("/api/v1/membership/check-entitlement")
def check_feature_entitlement(user_id: int = 1, feature_key: str = Query(...)):
    """Backend security boundary enforcing entitlement access controls."""
    return check_entitlement(user_id, feature_key)

@router.get("/api/v1/admin/memberships")
def admin_list_memberships():
    """Admin operational endpoint listing all user memberships."""
    return list_all_memberships()
