"""
BloodBridge AI — Standalone APScheduler Worker
===============================================
Runs the background scheduling jobs as a separate process.
Used by the Render.com worker service (render.yaml).

Start with:
    python -m scheduler.worker

Jobs registered:
  - Churn score recalculation (every 2 hours)
  - Leaderboard refresh (daily 2AM IST)
  - Stale chain detection (hourly)
  - Proactive outreach window check (daily 8AM/5PM IST)
"""
import time
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from scheduler.cron import setup_cron_jobs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("bloodbridge.worker")


def main():
    logger.info("╔══════════════════════════════════════════════╗")
    logger.info("║  BloodBridge AI — Background Worker Started  ║")
    logger.info("╚══════════════════════════════════════════════╝")

    scheduler = BlockingScheduler(timezone="Asia/Kolkata")
    setup_cron_jobs(scheduler)

    logger.info(f"Registered {len(scheduler.get_jobs())} background jobs. Starting...")
    for job in scheduler.get_jobs():
        logger.info(f"  • {job.name} — next run: {job.next_run_time}")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker shutdown signal received.")
        scheduler.shutdown()
        logger.info("Worker stopped cleanly.")


if __name__ == "__main__":
    main()
