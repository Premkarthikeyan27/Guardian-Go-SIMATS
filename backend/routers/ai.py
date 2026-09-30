from fastapi import APIRouter
from backend.services.ai_service import (
    check_ai_health,
    recommend_guardians_ai,
    generate_role_assistant,
    generate_admin_summary
)
from backend.schemas import AIQuestionRequest, AIRecommendationRequest

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

@router.get("/health")
async def ai_health():
    """Check Ollama connectivity & qwen3:4b model status (returns AI_AVAILABLE or AI_UNAVAILABLE)."""
    return await check_ai_health()

@router.post("/recommend-guardians")
async def ai_recommend_guardians(req: AIRecommendationRequest):
    """AI Guardian Recommendation engine powered by local Qwen 3:4B with explainable AI output."""
    return await recommend_guardians_ai(req.parent_id or 1, req.dependent_id, req.care_type or "Childcare")

@router.post("/assistant/user")
async def user_ai_assistant(req: AIQuestionRequest):
    """Parent AI Assistant."""
    return await generate_role_assistant(req.prompt, role="parent")

@router.post("/assistant/guardian")
async def guardian_ai_assistant(req: AIQuestionRequest):
    """Guardian AI Assistant."""
    return await generate_role_assistant(req.prompt, role="guardian")

@router.post("/assistant/admin")
async def admin_ai_assistant(req: AIQuestionRequest):
    """Admin AI Assistant."""
    return await generate_role_assistant(req.prompt, role="admin")

@router.get("/summary/admin")
async def admin_ai_summary():
    """Generate executive AI summary for Admin Command Centre dashboard."""
    return await generate_admin_summary()
