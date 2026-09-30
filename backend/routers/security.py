from fastapi import APIRouter
from backend.services.security_service import (
    get_security_health_status,
    mask_aadhaar,
    mask_phone,
    mask_email
)

router = APIRouter(prefix="/api/v1/security", tags=["security"])

@router.get("/health")
def fetch_security_health():
    """Retrieve Security Health Compliance Audit payload."""
    return get_security_health_status()

@router.post("/mask-test")
def test_data_masking(aadhaar: str = "998877665544", phone: str = "+1 555-0192", email: str = "sarah.jenkins@demo.com"):
    """Test sensitive PII masking functionality."""
    return {
        "original_aadhaar": aadhaar,
        "masked_aadhaar": mask_aadhaar(aadhaar),
        "original_phone": phone,
        "masked_phone": mask_phone(phone),
        "original_email": email,
        "masked_email": mask_email(email)
    }
