"""API router aggregation."""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    uploads,
    audit,
    monitoring,
    pipeline,
    health,
)

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(uploads.router, prefix="/uploads", tags=["File Uploads"])
router.include_router(audit.router, prefix="/audit", tags=["Audit Logs"])
router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])
router.include_router(pipeline.router, prefix="/pipeline", tags=["DevSecOps Pipeline"])
router.include_router(health.router, tags=["Health"])
