from fastapi import APIRouter
from backend.services.verification_service import get_guardians_list, get_verification_details
from backend.services.booking_service import check_in_session, check_out_session, add_routine_log, list_routine_logs
from backend.schemas import CheckInRequest, CheckOutRequest, RoutineCreate

router = APIRouter(tags=["guardian"])

@router.get("/api/v1/guardians")
def get_all_guardians():
    return get_guardians_list()

@router.get("/api/v1/verification")
def fetch_verification_records(guardian_id: int = 1):
    return get_verification_details(guardian_id)

@router.post("/api/v1/care-sessions/check-in")
def handle_check_in(req: CheckInRequest):
    return check_in_session(req.booking_id, req.guardian_id)

@router.post("/api/v1/care-sessions/check-out")
def handle_check_out(req: CheckOutRequest):
    return check_out_session(req.booking_id, req.guardian_id)

@router.post("/api/v1/care/routine")
def submit_routine(req: RoutineCreate):
    return add_routine_log(req.session_id or 1, req.guardian_id, req.category, req.title, req.details or "")

@router.get("/api/v1/care/routine")
def get_routines(guardian_id: int = 1, session_id: int = None):
    return list_routine_logs(guardian_id=guardian_id, session_id=session_id)
