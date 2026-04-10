from apscheduler.schedulers.asyncio import AsyncIOScheduler
from api.db.task import publish_scheduled_tasks
from api.cron import (
    check_memory_and_raise_alert,
)
from api.settings import settings
from datetime import timezone, timedelta
import logging
import sentry_sdk
from functools import wraps
from typing import Callable, Any

# Learning Network Platform imports (lazy to avoid circular at startup)
async def _run_content_staleness_check():
    from api.db.post import get_posts_for_staleness_check, update_post_lifecycle
    from datetime import datetime, timezone as tz
    posts = await get_posts_for_staleness_check()
    now = datetime.now(tz.utc)
    for post in posts:
        if not post.get("updated_at"):
            continue
        try:
            updated = datetime.fromisoformat(str(post["updated_at"]).replace("Z", "+00:00"))
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=tz.utc)
            days_inactive = (now - updated).days
            if post["lifecycle_status"] == "active" and days_inactive >= 28:
                await update_post_lifecycle(post["id"], "stale")
            elif post["lifecycle_status"] == "stale" and days_inactive >= 180:
                await update_post_lifecycle(post["id"], "archived")
        except (ValueError, TypeError):
            continue


async def _run_vote_ring_detection():
    from api.db.reputation import detect_vote_rings
    # org_id=0 means cross-org check (simplified — production would iterate orgs)
    suspicious = await detect_vote_rings(org_id=0)
    if suspicious:
        logging.warning(f"Vote ring detection: {len(suspicious)} suspicious pairs found")


async def _run_reputation_reconciliation():
    from api.db.reputation import recalculate_reputation
    from api.utils.db import execute_db_operation
    from api.config import user_reputation_table_name
    rows = await execute_db_operation(
        f"SELECT DISTINCT user_id, org_id FROM {user_reputation_table_name}",
        fetch_all=True,
    )
    for row in rows:
        try:
            await recalculate_reputation(row[0], row[1])
        except Exception as e:
            logging.error(f"Reputation reconciliation failed for user {row[0]}: {e}")

# Create IST timezone
ist_timezone = timezone(timedelta(hours=5, minutes=30))

scheduler = AsyncIOScheduler(timezone=ist_timezone)


def with_error_reporting(context: str):
    """Decorator to add Sentry error reporting to scheduled tasks"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logging.error(f"Error in scheduled task '{context}': {e}", exc_info=True)
                if settings.sentry_dsn:
                    sentry_sdk.capture_exception(e)
                raise

        return wrapper

    return decorator


# Check for tasks to publish every minute
@scheduler.scheduled_job("interval", minutes=1)
@with_error_reporting("scheduled_task_publish")
async def check_scheduled_tasks():
    await publish_scheduled_tasks()


@scheduler.scheduled_job("cron", hour=23, minute=55, timezone=ist_timezone)
@with_error_reporting("memory_check")
async def check_memory():
    await check_memory_and_raise_alert()


# ── Learning Network Platform Scheduled Jobs ───────────────────────────────────

@scheduler.scheduled_job("cron", hour=3, minute=0, timezone=ist_timezone)
@with_error_reporting("content_staleness_check")
async def content_staleness_check():
    """Daily: Mark posts as stale (28d inactive) or archived (180d inactive)."""
    await _run_content_staleness_check()


@scheduler.scheduled_job("cron", hour=4, minute=0, timezone=ist_timezone)
@with_error_reporting("vote_ring_detection")
async def vote_ring_detection():
    """Daily: Detect mutual voting patterns (anti-gaming)."""
    await _run_vote_ring_detection()


@scheduler.scheduled_job("cron", day_of_week="mon", hour=8, minute=0, timezone=ist_timezone)
@with_error_reporting("reputation_reconciliation")
async def reputation_reconciliation():
    """Weekly (Monday): Recalculate all reputation totals from event log."""
    await _run_reputation_reconciliation()
