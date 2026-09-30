from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from backend.schemas import FamilyMemberInviteRequest, RoutineCreate
from backend.services.family_service import (
    add_family_member,
    get_family_members,
    remove_family_member,
    add_care_routine,
    get_session_care_routines,
    get_guardian_care_routines
)

router = APIRouter(prefix="/api/v1/family", tags=["family"])

@router.post("/members")
def invite_member(req: FamilyMemberInviteRequest):
    """Invite an extended family member to the Family Circle with defined access level."""
    return add_family_member(
        parent_id=req.parent_id,
        name=req.name,
        email=req.email,
        relation=req.relation,
        access_level=req.access_level or "CARE_VIEWER"
    )

@router.get("/members/{parent_id}")
def fetch_family_members(parent_id: int):
    """Retrieve Family Circle members for a parent account."""
    return get_family_members(parent_id)

@router.delete("/members/{member_id}")
def delete_family_member(member_id: int, parent_id: int = Query(1)):
    """Revoke access for a Family Circle member."""
    return remove_family_member(member_id, parent_id)

@router.post("/routines")
def post_care_routine(req: RoutineCreate):
    """Log a structured care routine entry (Meal, Medication, Activity, Nap, Hygiene)."""
    return add_care_routine(
        session_id=req.session_id or 1,
        guardian_id=req.guardian_id or 1,
        category=req.category,
        title=req.title,
        details=req.details or ""
    )

@router.get("/routines/session/{session_id}")
def fetch_session_routines(session_id: int):
    """Fetch care routines logged during an active or completed care session."""
    return get_session_care_routines(session_id)

@router.get("/routines/guardian/{guardian_id}")
def fetch_guardian_routines(guardian_id: int):
    """Fetch all care routines logged by a specific guardian."""
    return get_guardian_care_routines(guardian_id)
