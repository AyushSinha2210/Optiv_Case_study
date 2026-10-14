"""Operational reporting, executive KPI metrics, and CSV export endpoints."""

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from src.cadence_tprm.database import get_db
from src.cadence_tprm.services.reporting_service import ReportingService
from src.cadence_tprm.services.auth_service import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Returns live KPI aggregations from actual relational database rows."""
    return ReportingService.get_dashboard_summary(db)

@router.get("/export/{report_type}")
def export_report(
    report_type: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Exports real CSV data for vendors, findings, assessments, or audit history."""
    csv_content = ReportingService.export_report_csv(db, report_type=report_type, actor_email=current_user["email"])
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="cadence_tprm_{report_type}_report.csv"'},
    )
