"""Operational reporting and executive KPI metrics endpoints."""

from fastapi import APIRouter, Depends
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
