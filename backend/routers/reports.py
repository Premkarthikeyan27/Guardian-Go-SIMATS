from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from backend.schemas import DailyReportCreate
from backend.services.care_report_service import (
    create_daily_report,
    get_daily_reports_for_parent,
    get_daily_reports_for_guardian,
    get_daily_report_by_id,
    refresh_report_ai_summary
)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

@router.post("")
async def post_daily_report(req: DailyReportCreate):
    """Create a structured Daily Care Report with Local Qwen AI summary."""
    return await create_daily_report(
        booking_id=req.booking_id,
        session_id=req.session_id,
        guardian_id=req.guardian_id,
        parent_id=req.parent_id,
        child_name=req.child_name,
        date=req.date,
        meals=req.meals,
        naps=req.naps,
        activities=req.activities,
        mood=req.mood,
        health_notes=req.health_notes,
        photos=req.photos
    )

@router.get("/parent/{parent_id}")
def fetch_parent_reports(parent_id: int):
    """Retrieve all daily care reports for a parent's timeline."""
    return get_daily_reports_for_parent(parent_id)

@router.get("/guardian/{guardian_id}")
def fetch_guardian_reports(guardian_id: int):
    """Retrieve all daily care reports logged by a guardian."""
    return get_daily_reports_for_guardian(guardian_id)

@router.get("/{report_id}")
def fetch_report(report_id: int):
    """Retrieve detailed view of a single daily care report."""
    report = get_daily_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Daily care report not found")
    return report

@router.post("/{report_id}/ai-summary")
async def trigger_ai_summary(report_id: int):
    """Regenerate or trigger Local Qwen AI summary & insights for a care report."""
    res = await refresh_report_ai_summary(report_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res
