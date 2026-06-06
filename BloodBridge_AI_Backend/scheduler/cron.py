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
    keep_alive_ping,
    run_blood_bank_cache_update,
    check_stale_voice_calls,
    run_daily_demand_forecast,
    run_monthly_churn_retrain
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
    scheduler.add_job(run_blood_bank_cache_update, IntervalTrigger(minutes=15), id='blood_bank_cache', replace_existing=True)
    # B3: Voice call retry + SMS fallback
    scheduler.add_job(check_stale_voice_calls, IntervalTrigger(minutes=15), id='voice_call_retry', replace_existing=True)
    # A3: Daily demand forecast at 6 AM IST (00:30 UTC)
    scheduler.add_job(run_daily_demand_forecast, CronTrigger(hour=0, minute=30), id='demand_forecast', replace_existing=True)
    # A4: Monthly churn retrain (1st of month, 2 AM IST = 20:30 UTC prev day)
    scheduler.add_job(run_monthly_churn_retrain, CronTrigger(day=1, hour=20, minute=30), id='churn_retrain', replace_existing=True)
