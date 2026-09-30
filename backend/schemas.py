from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class LoginRequest(BaseModel):
    email: str
    password: str

class ParentRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = None

class GuardianRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = None
    experience: Optional[str] = "1+ years experience"
    skills: Optional[str] = "First Aid, CPR"

class DependentCreate(BaseModel):
    parent_id: Optional[int] = 1
    name: str
    age: int
    special_needs: Optional[str] = "None"
    allergies: Optional[str] = "None"
    instructions: Optional[str] = ""

class DependentUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    special_needs: Optional[str] = None
    allergies: Optional[str] = None
    instructions: Optional[str] = None

class VerificationDocumentRequest(BaseModel):
    guardian_id: int
    document_type: str
    document_url: str
    notes: Optional[str] = None

class FaceVerifyRequest(BaseModel):
    guardian_id: int

class PoliceCheckRequest(BaseModel):
    guardian_id: int

class AddressVerifyRequest(BaseModel):
    guardian_id: int
    address_details: Optional[str] = None

class DigiLockerInitiateRequest(BaseModel):
    guardian_id: int

class DigiLockerConsentRequest(BaseModel):
    guardian_id: int
    auth_code: Optional[str] = "DEMO_OAUTH_CODE_2026"

class DigiLockerAdminVerifyRequest(BaseModel):
    guardian_id: int
    status_override: str  # 'VERIFIED', 'FAILED', 'REJECTED'
    reason: Optional[str] = "Admin document audit verification"

class MembershipSubscribeRequest(BaseModel):
    user_id: Optional[int] = 1
    plan: str  # 'BASIC_CARE', 'SAFECARE', 'PREMIUM_CARE_PLUS'
    payment_method: Optional[str] = "DEMO_CREDIT_CARD"

class MembershipUpgradeRequest(BaseModel):
    user_id: Optional[int] = 1
    new_plan: str

class MembershipCancelRequest(BaseModel):
    user_id: Optional[int] = 1

class EntitlementCheckRequest(BaseModel):
    user_id: Optional[int] = 1
    feature_key: str

class GuardianAvailabilitySetRequest(BaseModel):
    guardian_id: int
    date: str
    time_slots: List[str]
    service_types: Optional[List[str]] = ["Standard Care", "Pediatric Care"]
    specialization: Optional[str] = "Childcare"

class AIRecommendationRequest(BaseModel):
    parent_id: Optional[int] = 1
    dependent_id: Optional[int] = None
    care_type: Optional[str] = "Childcare"

class RiskAlertResolveRequest(BaseModel):
    action: str  # 'RESOLVE', 'DISMISS', 'SUSPEND_GUARDIAN'
    admin_notes: Optional[str] = None

class RiskEvaluateRequest(BaseModel):
    guardian_id: int

class BookingCreate(BaseModel):
    parent_id: int = 1
    guardian_id: int
    parent_name: Optional[str] = "Sarah Jenkins"
    date: str
    time: str
    care_type: str = "Standard Care"
    notes: Optional[str] = ""

class BookingStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None
    actor_name: Optional[str] = "User"

class CheckInRequest(BaseModel):
    booking_id: int
    guardian_id: int

class CheckOutRequest(BaseModel):
    booking_id: int
    guardian_id: int

class RoutineCreate(BaseModel):
    session_id: Optional[int] = 1
    guardian_id: int = 1
    category: str  # meal, medication, activity, nap, hygiene, note
    title: str
    details: Optional[str] = ""

class SOSRequest(BaseModel):
    user_id: Optional[int] = 1
    guardian_id: Optional[int] = 1
    latitude: Optional[float] = 37.7749
    longitude: Optional[float] = -122.4194
    notes: Optional[str] = "Emergency SOS button triggered"

class EmergencyStatusUpdateRequest(BaseModel):
    status: str  # DISPATCHED, RESPONDER_ON_SCENE, RESOLVED, DISMISSED
    notes: Optional[str] = None
    actor_name: Optional[str] = "Admin Dispatcher"


class BeaconSimulateRequest(BaseModel):
    action: str  # 'breach', 'reset', 'connect', 'warning'
    distance_m: Optional[float] = None
    rssi: Optional[int] = None

class AIQuestionRequest(BaseModel):
    prompt: str
    user_id: Optional[int] = 1

class AdminActionRequest(BaseModel):
    reason: Optional[str] = "Admin review completed"

class UserLoginRequest(BaseModel):
    email: str
    role: str

class DailyReportCreate(BaseModel):
    booking_id: int
    session_id: Optional[int] = None
    guardian_id: int
    parent_id: int = 1
    child_name: str
    date: str
    meals: Optional[Dict[str, Any]] = Field(default_factory=dict)
    naps: Optional[Dict[str, Any]] = Field(default_factory=dict)
    activities: Optional[List[str]] = Field(default_factory=list)
    mood: Optional[str] = "Happy & Energetic"
    health_notes: Optional[str] = "None"
    photos: Optional[List[str]] = Field(default_factory=list)

class NotificationSendRequest(BaseModel):
    user_id: int
    type: str  # BOOKING, CHECK_IN, BEACON, RISK, SOS, SYSTEM
    channel: Optional[str] = "PUSH"  # PUSH, SMS, EMAIL, BROADCAST
    title: str
    message: str

class FamilyMemberInviteRequest(BaseModel):
    parent_id: int = 1
    name: str
    email: str
    relation: str  # Grandparent, Co-Parent, Aunt/Uncle, Guardian, Emergency Contact
    access_level: Optional[str] = "CARE_VIEWER"  # FULL_ACCESS, CARE_VIEWER, EMERGENCY_ONLY

class ComplaintSubmitRequest(BaseModel):
    parent_id: int = 1
    guardian_id: int
    booking_id: Optional[int] = None
    complaint_text: str

class ComplaintResolveRequest(BaseModel):
    action: str  # 'DISMISS', 'INVESTIGATE', 'WARN_GUARDIAN', 'FLAG_FOR_AUDIT', 'SUSPEND_GUARDIAN'
    admin_notes: Optional[str] = None
    actor_name: Optional[str] = "Admin Officer"




