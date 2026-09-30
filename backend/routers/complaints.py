from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from backend.schemas import ComplaintSubmitRequest, ComplaintResolveRequest
from backend.services.complaint_service import (
    submit_complaint,
    get_all_complaints,
    get_parent_complaints,
    get_guardian_complaints,
    resolve_complaint
)

router = APIRouter(prefix="/api/v1/complaints", tags=["complaints"])

@router.post("")
async def post_complaint(req: ComplaintSubmitRequest):
    """Submit a complaint and run real-time NLP Sentiment, Risk Classification, and XAI Factor extraction."""
    return await submit_complaint(
        parent_id=req.parent_id,
        guardian_id=req.guardian_id,
        complaint_text=req.complaint_text,
        booking_id=req.booking_id
    )

@router.get("")
def list_complaints(status: Optional[str] = None, risk_level: Optional[str] = None):
    """List all complaints for Admin Command Center inspection with XAI factor breakdown."""
    return get_all_complaints(status=status, risk_level=risk_level)

@router.get("/parent/{parent_id}")
def list_parent_complaints(parent_id: int):
    """Retrieve all complaints submitted by a parent account."""
    return get_parent_complaints(parent_id)

@router.get("/guardian/{guardian_id}")
def list_guardian_complaints(guardian_id: int):
    """Retrieve all complaints logged regarding a specific guardian."""
    return get_guardian_complaints(guardian_id)

@router.post("/{complaint_id}/resolve")
def resolve_parent_complaint(complaint_id: int, req: ComplaintResolveRequest):
    """Admin resolution endpoint ('AI flags risk only; Admin decides'). Take action: DISMISS, WARN_GUARDIAN, INVESTIGATE, SUSPEND_GUARDIAN."""
    res = resolve_complaint(
        complaint_id=complaint_id,
        action=req.action,
        admin_notes=req.admin_notes,
        actor_name=req.actor_name or "Admin Officer"
    )
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res
