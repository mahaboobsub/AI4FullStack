"""
APScheduler Job registration for BloodBridge AI.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from scheduler.jobs import (
    monitor_all_active_chains,
    run_nightly_churn_batch,
    run_proactive_outreach,
    cleanup_old_voice_files,
    keep_alive_ping
)

_global_scheduler = None

def get_global_scheduler() -> AsyncIOScheduler:
    """Retrieve the active global scheduler instance or initialize a fallback."""
    global _global_scheduler
    if _global_scheduler is None:
        logger = logging.getLogger("bloodbridge.scheduler")
        logger.info("Initializing stand-alone fallback AsyncIOScheduler...")
        _global_scheduler = AsyncIOScheduler()
        _global_scheduler.start()
    return _global_scheduler

def setup_cron_jobs(scheduler: AsyncIOScheduler):
    """Register all recurring cron and interval jobs to the scheduler."""
    global _global_scheduler
    _global_scheduler = scheduler
    scheduler.add_job(monitor_all_active_chains, IntervalTrigger(minutes=5), id='chain_monitor', replace_existing=True)
    scheduler.add_job(run_nightly_churn_batch, CronTrigger(hour=20, minute=0), id='churn_batch', replace_existing=True)
    scheduler.add_job(run_proactive_outreach, CronTrigger(hour=7, minute=0), id='proactive_outreach', replace_existing=True)
    scheduler.add_job(cleanup_old_voice_files, CronTrigger(hour=2, minute=0), id='voice_cleanup', replace_existing=True)
    scheduler.add_job(keep_alive_ping, IntervalTrigger(minutes=4), id='keep_alive', replace_existing=True)
