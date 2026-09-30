from fastapi import APIRouter
from backend.services.beacon_service import get_beacon_status, simulate_beacon
from backend.schemas import BeaconSimulateRequest

router = APIRouter(prefix="/api/v1/beacon", tags=["beacon"])

@router.get("/status")
def fetch_beacon_status(beacon_id: int = 1):
    return get_beacon_status(beacon_id=beacon_id)

@router.post("/simulate")
def post_simulate_beacon(req: BeaconSimulateRequest):
    return simulate_beacon(
        action=req.action,
        distance_m=req.distance_m,
        rssi=req.rssi
    )
