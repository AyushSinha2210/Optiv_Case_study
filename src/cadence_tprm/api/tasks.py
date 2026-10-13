"""Tasks, notifications, and SLA automation endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from src.cadence_tprm.database import get_db
from src.cadence_tprm.models.task import Task, Notification
from src.cadence_tprm.services.sla_service import SLAService
from src.cadence_tprm.services.auth_service import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("")
def list_tasks(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(Task)
    
    # Filter for tasks relevant to this user or their groups
    user_email = current_user["email"]
    user_groups = current_user.get("groups", [])
    
    if not current_user.get("is_admin"):
        query = query.filter(
            (Task.assignee_email == user_email) |
            (Task.collaborator_group.in_(user_groups))
        )

    if status_filter:
        query = query.filter(Task.status == status_filter)

    tasks = query.order_by(Task.due_date.asc()).all()
    now = datetime.now(timezone.utc)

    return {
        "tasks": [
            {
                "id": t.id,
                "vendor_id": t.vendor_id,
                "vendor_name": t.vendor.name if t.vendor else "",
                "assessment_id": t.assessment_id,
                "task_type": t.task_type,
                "title": t.title,
                "description": t.description,
                "assignee_email": t.assignee_email,
                "collaborator_group": t.collaborator_group,
                "due_date": t.due_date.isoformat(),
                "is_overdue": t.due_date.replace(tzinfo=timezone.utc) < now if t.status == "Pending" else False,
                "status": t.status,
                "created_at": t.created_at.isoformat(),
            }
            for t in tasks
        ]
    }

@router.post("/{task_id}/complete")
def complete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    task = db.query(Task).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "Completed"
    task.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "completed", "task_id": task_id}

@router.get("/notifications")
def list_notifications(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_email = current_user["email"]
    notifications = (
        db.query(Notification)
        .filter(
            (Notification.recipient_email == user_email) |
            (Notification.recipient_email == "system@cadence.com")
        )
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return {
        "notifications": [
            {
                "id": n.id,
                "subject": n.subject,
                "body": n.body,
                "is_read": n.is_read,
                "link_url": n.link_url,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ]
    }

@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    notif = db.query(Notification).filter_by(id=notification_id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"status": "read"}

@router.post("/automation/run-reassessments")
def trigger_reassessments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Manually triggers the daily automation runner for AR.T1.1, AR.T2.1, AR.T3.1."""
    results = SLAService.run_daily_reassessment_automation(db, actor_email=current_user["email"])
    reminders = SLAService.process_sla_reminders(db)
    return {
        "status": "success",
        "automation_results": results,
        "sla_reminders_sent": reminders
    }
