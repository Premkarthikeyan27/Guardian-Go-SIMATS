from fastapi import APIRouter, HTTPException
from backend.services.verification_service import (
    get_guardian_passport,
    submit_verification_document,
    verify_face_and_liveness,
    verify_police_clearance,
    verify_address,
    get_verification_details
)
from backend.schemas import (
    VerificationDocumentRequest,
    FaceVerifyRequest,
    PoliceCheckRequest,
    AddressVerifyRequest
)

router = APIRouter(prefix="/api/v1/verification", tags=["verification"])

@router.get("/passport/{guardian_id}")
def fetch_guardian_passport(guardian_id: int):
    """Retrieve Digital Guardian Passport."""
    passport = get_guardian_passport(guardian_id)
    if not passport:
        raise HTTPException(status_code=404, detail=f"Guardian #{guardian_id} passport not found")
    return passport

@router.post("/upload")
def upload_verification_doc(req: VerificationDocumentRequest):
    """Submit document for 4-Gate verification review."""
    return submit_verification_document(req.guardian_id, req.document_type, req.document_url, req.notes)

@router.post("/face-verify")
def perform_face_and_liveness(req: FaceVerifyRequest):
    """Perform face & anti-spoof liveness check abstraction."""
    return verify_face_and_liveness(req.guardian_id)

@router.post("/police-verify")
def perform_police_check(req: PoliceCheckRequest):
    """Perform national police clearance database abstraction check."""
    return verify_police_clearance(req.guardian_id)

@router.post("/address-verify")
def perform_address_check(req: AddressVerifyRequest):
    """Perform address verification abstraction check."""
    return verify_address(req.guardian_id, req.address_details)

@router.get("/status/{guardian_id}")
def fetch_verification_status(guardian_id: int):
    """Fetch 4-Gate verification status & submitted records."""
    return get_verification_details(guardian_id)
