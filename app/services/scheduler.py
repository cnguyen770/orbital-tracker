from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.tle_client import fetch_tle_group
from app.services.satellite_service import upsert_satellites
from app.core.database import AsyncSessionLocal
import logging

logger = logging.getLogger(__name__)

GROUPS_TO_SYNC = ["stations", "weather", "starlink"]

scheduler = AsyncIOScheduler()


async def refresh_all_groups():
    logger.info("Scheduled TLE refresh starting...")
    async with AsyncSessionLocal() as db:
        for group in GROUPS_TO_SYNC:
            try:
                satellites = await fetch_tle_group(group)
                count = await upsert_satellites(db, satellites, group)
                logger.info(f"Refreshed {count} satellites for group '{group}'")
            except Exception as e:
                logger.error(f"Failed to refresh group '{group}': {e}")

    logger.info("Scheduled TLE refresh complete")


def start_scheduler():
    scheduler.add_job(
        refresh_all_groups,
        trigger=IntervalTrigger(hours=24),
        id="tle_refresh",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — TLE refresh every 24 hours")