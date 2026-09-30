from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.services.safety_service import (
    trigger_sos,
    get_safety_events,
    resolve_safety_event,
    get_safety_centre_status,
    update_emergency_status,
    get_emergency_case_file,
    MockFingerprintService,
    MockFaceVerificationService
)
from backend.schemas import SOSRequest, EmergencyStatusUpdateRequest

router = APIRouter(prefix="/api/v1/safety", tags=["safety"])

@router.get("/centre/{parent_id}")
def fetch_safety_centre(parent_id: int):
    """Retrieve consolidated Parent Safety Centre status, BLE beacon signal, biometrics, and active session."""
    return get_safety_centre_status(parent_id)

@router.post("/fingerprint/enroll")
def enroll_fingerprint(guardian_id: int = Query(...)):
    """Fingerprint scanner hardware enrollment abstraction."""
    return MockFingerprintService.enroll_guardian(guardian_id)

@router.post("/fingerprint/verify")
def verify_fingerprint(guardian_id: int = Query(...)):
    """Fingerprint scanner biometric verification abstraction check."""
    return MockFingerprintService.verify_guardian(guardian_id)

@router.post("/face/liveness")
def check_face_liveness(guardian_id: int = Query(...)):
    """Facial recognition & anti-spoof liveness check abstraction."""
    return MockFaceVerificationService.check_face_and_liveness(guardian_id)

@router.post("/sos")
@router.post("/emergency/trigger")
def post_emergency_trigger(req: SOSRequest):
    """Trigger 1-Tap Emergency SOS Alert with live GPS, multi-channel family broadcast, and incident case reference."""
    return trigger_sos(
        user_id=req.user_id or 1,
        guardian_id=req.guardian_id or 1,
        latitude=req.latitude,
        longitude=req.longitude,
        notes=req.notes or ""
    )

@router.get("/emergency/active")
def list_active_emergencies():
    """Retrieve list of all active emergency incidents."""
    return get_safety_events(status="ACTIVE")

@router.get("/emergency/{incident_id}")
def fetch_emergency_case(incident_id: int):
    """Retrieve complete Emergency Case File including user, guardian, and live BLE beacon status."""
    res = get_emergency_case_file(incident_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.post("/emergency/{incident_id}/status")
def update_emergency_incident_status(incident_id: int, req: EmergencyStatusUpdateRequest):
    """Update Emergency Protocol Status (DISPATCHED, RESPONDER_ON_SCENE, RESOLVED, DISMISSED)."""
    res = update_emergency_status(
        event_id=incident_id,
        status=req.status,
        notes=req.notes,
        actor_name=req.actor_name or "Admin Dispatcher"
    )
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.get("/events")
def list_events(status: Optional[str] = None):
    """List safety monitoring events."""
    return get_safety_events(status=status)

@router.post("/events/{id}/resolve")
def resolve_event(id: int):
    """Resolve a safety event."""
    return resolve_safety_event(id, actor_name="Admin")
