from fastapi import APIRouter, HTTPException
from backend.schemas import NotificationSendRequest
from backend.services.notification_service import (
    send_notification,
    get_user_notifications,
    mark_notification_as_read,
    mark_all_notifications_as_read
)

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

@router.get("/{user_id}")
def fetch_notifications(user_id: int):
    """Retrieve notifications list and unread count for a user."""
    return get_user_notifications(user_id)

@router.post("/send")
def post_notification(req: NotificationSendRequest):
    """Dispatch a multi-channel notification (PUSH, SMS, EMAIL, BROADCAST)."""
    return send_notification(
        user_id=req.user_id,
        type=req.type,
        title=req.title,
        message=req.message,
        channel=req.channel or "PUSH"
    )

@router.post("/{notification_id}/read")
def mark_read(notification_id: int):
    """Mark a single notification as read."""
    res = mark_notification_as_read(notification_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.post("/read-all/{user_id}")
def mark_all_read(user_id: int):
    """Mark all notifications for a user as read."""
    return mark_all_notifications_as_read(user_id)
