from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.services.booking_service import (
    list_bookings,
    create_booking,
    update_booking_status,
    search_guardians,
    set_guardian_availability,
    get_guardian_availability
)
from backend.schemas import (
    BookingCreate,
    BookingStatusUpdate,
    GuardianAvailabilitySetRequest
)

router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])

@router.get("")
@router.get("/")
def get_bookings(role: Optional[str] = None, user_id: Optional[int] = None, status: Optional[str] = None):
    """Fetch booking history with optional role, user, and status filters."""
    return list_bookings(role=role, user_id=user_id, status_filter=status)

@router.post("")
@router.post("/")
def make_booking(req: BookingCreate):
    """Create new booking request with schedule conflict prevention."""
    try:
        return create_booking(
            parent_id=req.parent_id,
            guardian_id=req.guardian_id,
            parent_name=req.parent_name or "Sarah Jenkins",
            date_str=req.date,
            time_str=req.time,
            care_type=req.care_type,
            notes=req.notes or ""
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/{id}/status")
def change_booking_status(id: int, req: BookingStatusUpdate):
    """Update booking lifecycle status (REQUESTED -> CONFIRMED -> CHECKED_IN -> COMPLETED/CANCELLED)."""
    try:
        return update_booking_status(id, req.status, actor_name=req.actor_name or "User")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{id}/accept")
def accept_booking(id: int):
    return update_booking_status(id, "ACCEPTED", actor_name="Guardian")

@router.post("/{id}/decline")
def decline_booking(id: int):
    return update_booking_status(id, "CANCELLED", actor_name="Guardian")

@router.get("/guardians/search")
def search_and_filter_guardians(
    query: Optional[str] = None,
    service_type: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_rate: Optional[float] = None
):
    """Search & filter verified guardians by keyword, service type, rating, and hourly rate."""
    return search_guardians(
        query=query,
        service_type=service_type,
        min_rating=min_rating,
        max_rate=max_rate
    )

@router.post("/availability")
def set_availability(req: GuardianAvailabilitySetRequest):
    """Set or update guardian availability for specific date & time slots."""
    return set_guardian_availability(
        guardian_id=req.guardian_id,
        date_str=req.date,
        time_slots=req.time_slots,
        service_types=req.service_types,
        specialization=req.specialization or "Childcare"
    )

@router.get("/availability/{guardian_id}")
def get_availability(guardian_id: int, date: Optional[str] = None):
    """Get availability schedule for a guardian."""
    return get_guardian_availability(guardian_id, date)
