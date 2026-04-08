from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.infrastructure.scheduler import (
    _run_snapshot_job,
    scheduler,
    start_scheduler,
    stop_scheduler,
)


class TestSchedulerLifecycle:
    async def test_start_registers_snapshot_job(self) -> None:
        try:
            start_scheduler()

            job = scheduler.get_job("snapshot_job")
            assert job is not None
            assert job.name == "Periodic weather snapshot"
        finally:
            stop_scheduler()

    async def test_start_is_idempotent(self) -> None:
        """Calling start twice should replace the job, not duplicate it."""
        try:
            start_scheduler()
            start_scheduler()  # should not raise

            jobs = scheduler.get_jobs()
            snapshot_jobs = [j for j in jobs if j.id == "snapshot_job"]
            assert len(snapshot_jobs) == 1
        finally:
            stop_scheduler()

    async def test_stop_is_safe_when_not_running(self) -> None:
        """stop_scheduler should not raise if scheduler is already stopped."""
        stop_scheduler()  # no-op, should not raise


class TestSnapshotJobRegistration:
    async def test_job_uses_interval_trigger(self) -> None:
        try:
            start_scheduler()
            job = scheduler.get_job("snapshot_job")
            assert job is not None
            assert isinstance(job.trigger, IntervalTrigger)
        finally:
            stop_scheduler()

    async def test_job_function_is_run_snapshot(self) -> None:
        try:
            start_scheduler()
            job = scheduler.get_job("snapshot_job")
            assert job is not None
            assert job.func is _run_snapshot_job
        finally:
            stop_scheduler()
