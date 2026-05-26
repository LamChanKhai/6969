"""DevSecOps pipeline service."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import PipelineStage, PipelineRun


async def get_pipeline_stages(db: AsyncSession) -> List[PipelineStage]:
    """Get all pipeline stages ordered."""
    result = await db.execute(
        select(PipelineStage).where(PipelineStage.is_active == True).order_by(PipelineStage.stage_order)
    )
    return result.scalars().all()


async def get_latest_pipeline_runs(db: AsyncSession) -> List[PipelineRun]:
    """Get latest run for each stage."""
    from sqlalchemy import text
    result = await db.execute(
        text("""
            SELECT pr.* FROM pipeline_runs pr
            INNER JOIN (
                SELECT stage_id, MAX(run_number) as max_run
                FROM pipeline_runs
                GROUP BY stage_id
            ) latest ON pr.stage_id = latest.stage_id AND pr.run_number = latest.max_run
            ORDER BY (
                SELECT ps.stage_order FROM pipeline_stages ps WHERE ps.id = pr.stage_id
            )
        """)
    )
    return result.scalars().all()


async def create_stage(db: AsyncSession, name: str, order: int, description: str = "") -> PipelineStage:
    """Create a pipeline stage."""
    stage = PipelineStage(
        stage_name=name,
        stage_order=order,
        description=description,
    )
    db.add(stage)
    await db.commit()
    await db.refresh(stage)
    return stage


async def create_run(
    db: AsyncSession,
    stage_id: uuid.UUID,
    run_number: int,
    status: str = "running",
    logs: str = "",
) -> PipelineRun:
    """Create a pipeline run."""
    run = PipelineRun(
        stage_id=stage_id,
        run_number=run_number,
        status=status,
        logs=logs,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


async def update_run_status(
    db: AsyncSession,
    run_id: uuid.UUID,
    status: str,
    logs: Optional[str] = None,
) -> Optional[PipelineRun]:
    """Update pipeline run status."""
    result = await db.execute(select(PipelineRun).where(PipelineRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        return None
    run.status = status
    if logs is not None:
        run.logs = logs
    if status in ("success", "failed", "skipped"):
        run.finished_at = datetime.now(timezone.utc)
        if run.started_at:
            run.duration_seconds = (run.finished_at - run.started_at).total_seconds()
    await db.commit()
    await db.refresh(run)
    return run


async def get_overall_status(db: AsyncSession) -> str:
    """Determine overall pipeline status from latest runs."""
    from sqlalchemy import text
    result = await db.execute(
        text("""
            SELECT pr.status FROM pipeline_runs pr
            INNER JOIN (
                SELECT stage_id, MAX(run_number) as max_run
                FROM pipeline_runs
                GROUP BY stage_id
            ) latest ON pr.stage_id = latest.stage_id AND pr.run_number = latest.max_run
        """)
    )
    statuses = [row[0] for row in result.fetchall()]
    if not statuses:
        return "idle"
    if "failed" in statuses:
        return "failed"
    if "running" in statuses:
        return "running"
    if all(s == "success" for s in statuses):
        return "success"
    return "partial"
