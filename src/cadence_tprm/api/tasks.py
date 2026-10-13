"""Tasks, notifications, and SLA automation endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from src.cadence_tprm.database import get_db
from src.cadence_tprm.models.task import Task, Notification
from src.cadence_tprm.models.vendor import Vendor
from src.cadence_tprm.services.sla_service import SLAService
from src.cadence_tprm.services.audit_service import AuditService
from src.cadence_tprm.services.auth_service import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("")
def list_tasks(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    query = db.query(Task)

    if status_filter and status_filter != "All":
        query = query.filter(Task.status == status_filter)

    tasks = query.order_by(Task.due_date.asc()).all()
    now = datetime.now(timezone.utc)

    items = []
    for t in tasks:
        v = db.query(Vendor).filter_by(id=t.vendor_id).first()
        due_dt = t.due_date.replace(tzinfo=timezone.utc) if t.due_date and t.due_date.tzinfo is None else t.due_date
        is_overdue = (due_dt < now) if (due_dt and t.status == "Pending") else False
        items.append({
            "id": t.id,
            "vendor_id": t.vendor_id,
            "vendor_name": v.name if v else "",
            "assessment_id": t.assessment_id,
            "task_type": t.task_type,
            "title": t.title,
            "description": t.description,
            "assignee_email": t.assignee_email,
            "collaborator_group": t.collaborator_group,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "reminder_date": t.reminder_date.isoformat() if t.reminder_date else None,
            "is_overdue": is_overdue,
            "status": t.status,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        })

    return {"tasks": items, "items": items, "total": len(items)}

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
    AuditService.log_event(
        db,
        actor_email=current_user["email"],
        action="TASK_COMPLETED",
        entity_type="TASK",
        entity_id=task.id,
        details={"title": task.title, "task_type": task.task_type, "vendor_id": task.vendor_id}
    )
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
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    # Show notifications for the current user or general system/VRM admin notifications
    filtered = [
        n for n in notifications
        if current_user.get("is_admin") or n.recipient_email in [user_email, "system@cadence.com"]
    ]
    items = [
        {
            "id": n.id,
            "recipient_email": n.recipient_email,
            "subject": n.subject,
            "body": n.body,
            "is_read": n.is_read,
            "link_url": n.link_url,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in filtered
    ]
    return {"notifications": items, "items": items}

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
    return {"status": "read", "notification_id": notification_id}

@router.post("/automation/run-reassessments")
def trigger_reassessments(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Manually triggers the daily automation runner for AR.T1.1, AR.T2.1, AR.T3.1 and SLA reminders."""
    results = SLAService.run_daily_reassessment_automation(db, actor_email=current_user["email"])
    reminders = SLAService.process_sla_reminders(db)
    total_reassessments = (
        results.get("tier1_reassessments", 0)
        + results.get("tier2_reassessments", 0)
        + results.get("tier3_reassessments", 0)
    )
    return {
        "status": "success",
        "automation_results": results,
        "sla_reminders_sent": reminders,
        "reassessments_created": total_reassessments,
        "notifications_sent": (total_reassessments * 2) + reminders,
    }
