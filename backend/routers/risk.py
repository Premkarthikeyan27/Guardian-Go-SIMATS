from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.services.trust_risk_service import (
    calculate_trust_score,
    evaluate_risk_and_fraud,
    list_risk_alerts,
    admin_resolve_risk_alert
)
from backend.schemas import RiskAlertResolveRequest, RiskEvaluateRequest

router = APIRouter(tags=["trust_risk"])

@router.get("/api/v1/trust/score/{guardian_id}")
def fetch_guardian_trust_score(guardian_id: int):
    """Retrieve evidence-based Trust Score with explainable factor breakdown."""
    score_data = calculate_trust_score(guardian_id)
    if not score_data:
        raise HTTPException(status_code=404, detail=f"Guardian #{guardian_id} not found")
    return score_data

@router.get("/api/v1/admin/risk/alerts")
def fetch_risk_alerts(status: Optional[str] = None):
    """Fetch active risk and fraud alerts for Admin Command Centre."""
    return list_risk_alerts(status_filter=status)

@router.post("/api/v1/admin/risk/evaluate/{guardian_id}")
async def trigger_ai_risk_evaluation(guardian_id: int):
    """Trigger AI & rule-based risk evaluation for a guardian (AI flags only, Admin decides)."""
    return await evaluate_risk_and_fraud(guardian_id)

@router.post("/api/v1/admin/risk/alerts/{id}/resolve")
def resolve_risk_alert(id: int, req: RiskAlertResolveRequest):
    """Admin workflow action to resolve, dismiss, or enforce guardian suspension."""
    return admin_resolve_risk_alert(id, req.action, req.admin_notes)
