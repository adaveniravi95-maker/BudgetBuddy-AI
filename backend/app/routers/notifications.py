from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..database import get_db
from .. import models, schemas, auth

router = APIRouter()


@router.get("/", response_model=schemas.NotificationListResponse)
def list_notifications(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
    )
    notifications = query.order_by(desc(models.Notification.created_at)).all()
    unread_count = sum(1 for n in notifications if not n.is_read)
    return schemas.NotificationListResponse(
        notifications=notifications,
        total=len(notifications),
        unread_count=unread_count,
    )


@router.get("/unread/", response_model=schemas.NotificationListResponse)
def list_unread_notifications(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.is_read == False,
    )
    notifications = query.order_by(desc(models.Notification.created_at)).all()
    return schemas.NotificationListResponse(
        notifications=notifications,
        total=len(notifications),
        unread_count=len(notifications),
    )


@router.put("/{notification_id}/read/")
def mark_notification_read(
    notification_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.id,
    ).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()
    return {"detail": "Notification marked as read"}


@router.put("/read-all/")
def mark_all_notifications_read(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"detail": "All notifications marked as read"}
