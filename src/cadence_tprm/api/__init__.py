"""API routers package."""

from fastapi import APIRouter
from src.cadence_tprm.api.auth import router as auth_router
from src.cadence_tprm.api.vendors import router as vendors_router
from src.cadence_tprm.api.questionnaires import router as questionnaires_router
from src.cadence_tprm.api.assessments import router as assessments_router
from src.cadence_tprm.api.workflows import router as workflows_router
from src.cadence_tprm.api.tasks import router as tasks_router
from src.cadence_tprm.api.integrations import router as integrations_router
from src.cadence_tprm.api.reports import router as reports_router
from src.cadence_tprm.api.audit import router as audit_router

api_router = APIRouter(prefix="/api/tprm/v1")
api_router.include_router(auth_router)
api_router.include_router(vendors_router)
api_router.include_router(questionnaires_router)
api_router.include_router(assessments_router)
api_router.include_router(workflows_router)
api_router.include_router(tasks_router)
api_router.include_router(integrations_router)
api_router.include_router(reports_router)
api_router.include_router(audit_router)

__all__ = ["api_router"]
