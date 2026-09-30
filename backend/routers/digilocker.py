from fastapi import APIRouter, HTTPException
from backend.services.digilocker_service import (
    MockDigiLockerService,
    get_digilocker_status,
    admin_override_digilocker
)
from backend.schemas import (
    DigiLockerInitiateRequest,
    DigiLockerConsentRequest,
    DigiLockerAdminVerifyRequest
)

router = APIRouter(prefix="/api/v1/digilocker", tags=["digilocker"])

@router.post("/initiate")
def initiate_consent(req: DigiLockerInitiateRequest):
    """Initiate DigiLocker OAuth2 consent flow for Guardian."""
    return MockDigiLockerService.generate_consent_url(req.guardian_id)

@router.post("/consent")
def complete_consent(req: DigiLockerConsentRequest):
    """Complete DigiLocker consent callback & fetch verified government documents."""
    return MockDigiLockerService.complete_consent_and_verify(req.guardian_id, req.auth_code)

@router.get("/status/{guardian_id}")
def fetch_status(guardian_id: int):
    """Fetch DigiLocker verification status, Aadhaar mask, and mode (DEMO vs LIVE)."""
    return get_digilocker_status(guardian_id)

@router.get("/documents/{guardian_id}")
def fetch_documents(guardian_id: int):
    """Fetch list of verified documents pulled from DigiLocker API."""
    status_data = get_digilocker_status(guardian_id)
    return {
        "guardian_id": guardian_id,
        "verified_name": status_data.get("verified_name"),
        "documents": status_data.get("documents_found", []),
        "mode": status_data.get("mode")
    }

@router.post("/admin/verify")
def admin_verify(req: DigiLockerAdminVerifyRequest):
    """Admin workflow endpoint to approve, override, or reject DigiLocker verification."""
    return admin_override_digilocker(req.guardian_id, req.status_override, req.reason)
