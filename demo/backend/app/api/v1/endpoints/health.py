"""Health check endpoint."""

from fastapi import APIRouter

from app.schemas.schemas import HealthCheckResponse

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Basic health check for load balancers and orchestrators."""
    return HealthCheckResponse()
