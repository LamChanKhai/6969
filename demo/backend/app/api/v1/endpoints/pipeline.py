"""DevSecOps pipeline visualization endpoints."""

import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_viewer_or_higher
from app.services.pipeline_service import (
    get_pipeline_stages,
    get_latest_pipeline_runs,
    get_overall_status,
)
from app.schemas.schemas import (
    PipelineOverviewResponse,
    PipelineStageResponse,
    PipelineRunResponse,
)

router = APIRouter()


@router.get("/overview", response_model=PipelineOverviewResponse)
async def pipeline_overview(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_viewer_or_higher),
):
    """Get pipeline overview with stages and latest runs."""
    stages = await get_pipeline_stages(db)
    latest_runs = await get_latest_pipeline_runs(db)
    overall_status = await get_overall_status(db)

    # Build stage name lookup
    stage_names = {str(s.id): s.stage_name for s in stages}

    runs_data = []
    for run in latest_runs:
        runs_data.append(PipelineRunResponse(
            id=run.id,
            stage_name=stage_names.get(str(run.stage_id), "Unknown"),
            run_number=run.run_number,
            status=run.status,
            started_at=run.started_at,
            finished_at=run.finished_at,
            duration_seconds=run.duration_seconds,
            logs=run.logs,
        ))

    return PipelineOverviewResponse(
        stages=[PipelineStageResponse.model_validate(s) for s in stages],
        latest_runs=runs_data,
        overall_status=overall_status,
    )
