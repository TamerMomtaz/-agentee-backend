"""
A-GENTEE Scheduler — Phase 3
Automated jobs: GuardTee checks, daily digest, stale task reminders.
Uses APScheduler in-process (AsyncIOScheduler) — no extra service cost.
"""

import logging
import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("agentee.scheduler")

scheduler = AsyncIOScheduler(timezone="Africa/Cairo")


async def guard_check_job(app):
    """Run GuardTee health check on all monitored services."""
    try:
        from api.guard import _run_checks
        results = await _run_checks()
        healthy = sum(1 for r in results if r.get("status") == "healthy")
        total = len(results)
        logger.info(f"⏰ GuardTee auto-check: {healthy}/{total} healthy")

        # If any service is down, push notification
        if healthy < total:
            unhealthy = [r["service"] for r in results if r.get("status") != "healthy"]
            push_mod = getattr(app.state, "push_module", None)
            if push_mod:
                await push_mod.notify_all(
                    title="🔴 GuardTee Alert",
                    body=f"Services down: {', '.join(unhealthy)}",
                    url="/guard"
                )
    except Exception as e:
        logger.error(f"GuardTee auto-check failed: {e}")


async def digest_push_job(app):
    """Generate daily digest and push to all subscribers."""
    try:
        from memory import memory
        digest = await memory.generate_digest()
        if digest:
            push_mod = getattr(app.state, "push_module", None)
            if push_mod:
                summary = digest.get("summary", "Your daily A-GENTEE digest is ready.")
                # Truncate for push body
                body = summary[:120] + "..." if len(summary) > 120 else summary
                await push_mod.notify_all(
                    title="📋 Daily Digest — A-GENTEE",
                    body=body,
                    url="/digest"
                )
            logger.info("⏰ Daily digest generated and pushed")
        else:
            logger.info("⏰ Daily digest: no conversations to summarize")
    except Exception as e:
        logger.error(f"Daily digest job failed: {e}")


async def stale_reminder_job(app):
    """Check for insights/tasks older than 3 days that haven't been actioned."""
    try:
        from memory import memory
        suggestions = await memory.get_proactive_suggestions()
        stale_tasks = [s for s in suggestions if s.get("type") == "stale_task"]

        if stale_tasks:
            push_mod = getattr(app.state, "push_module", None)
            if push_mod:
                count = len(stale_tasks)
                first = stale_tasks[0].get("content", "")[:80]
                await push_mod.notify_all(
                    title=f"⚡ {count} stale task{'s' if count > 1 else ''} need attention",
                    body=first + ("..." if len(first) >= 80 else ""),
                    url="/insights"
                )
            logger.info(f"⏰ Stale reminder: {len(stale_tasks)} tasks flagged")
        else:
            logger.info("⏰ Stale reminder: all tasks fresh ✅")
    except Exception as e:
        logger.error(f"Stale reminder job failed: {e}")


def start_scheduler(app):
    """Register all scheduled jobs and start the scheduler."""

    # GuardTee auto-check: every 15 minutes
    scheduler.add_job(
        guard_check_job,
        trigger=IntervalTrigger(minutes=15),
        args=[app],
        id="guardtee_autocheck",
        name="GuardTee Auto-Check",
        replace_existing=True,
        max_instances=1
    )

    # Daily digest: 06:00 UTC = 08:00 Cairo
    scheduler.add_job(
        digest_push_job,
        trigger=CronTrigger(hour=6, minute=0, timezone="UTC"),
        args=[app],
        id="daily_digest",
        name="Daily Digest + Push",
        replace_existing=True,
        max_instances=1
    )

    # Stale task reminder: 09:00 UTC = 11:00 Cairo
    scheduler.add_job(
        stale_reminder_job,
        trigger=CronTrigger(hour=9, minute=0, timezone="UTC"),
        args=[app],
        id="stale_reminder",
        name="Stale Task Reminder",
        replace_existing=True,
        max_instances=1
    )

    scheduler.start()
    logger.info("🕐 Scheduler started — 3 jobs registered")
    logger.info("   → GuardTee auto-check: every 15 min")
    logger.info("   → Daily digest + push: 08:00 Cairo")
    logger.info("   → Stale task reminder: 11:00 Cairo")


def stop_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("🕐 Scheduler stopped")
