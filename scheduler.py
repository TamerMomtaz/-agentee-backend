"""
A-GENTEE Scheduler — Phase 3
Automated jobs: GuardTee checks, daily digest, stale task reminders.
Uses APScheduler in-process (AsyncIOScheduler) — no extra service cost.
"""

import logging
import os
import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("agentee.scheduler")

scheduler = AsyncIOScheduler(timezone="Africa/Cairo")


async def guard_check_job(app):
    """Run GuardTee health check by directly calling _check_service (pure async, no Request needed)."""
    try:
        from api.guard import _check_service, SERVICES

        tasks = [_check_service(svc) for svc in SERVICES]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        checks = [r for r in results if not isinstance(r, Exception)]
        healthy = sum(1 for c in checks if c.get("status") == "healthy")
        total = len(checks)
        logger.info(f"⏰ GuardTee auto-check: {healthy}/{total} healthy")

        # If any service is down or degraded, push notification
        down = [c for c in checks if c.get("status") not in ("healthy",)]
        if down:
            names = [c["service_name"] for c in down]
            push_mod = getattr(app.state, "push_module", None)
            if push_mod:
                await push_mod.send_to_all_subscribers(
                    title="🛡️ GuardTee Alert",
                    body=f"Issue: {', '.join(names)}",
                    app=app,
                )
    except Exception as e:
        logger.error(f"GuardTee auto-check failed: {e}")


async def digest_push_job(app):
    """Generate daily digest via HTTP and push to subscribers."""
    import httpx

    try:
        port = os.environ.get("PORT", "8000")
        async with httpx.AsyncClient() as client:
            res = await client.post(f"http://127.0.0.1:{port}/api/v1/digest", timeout=60)
            digest = res.json() if res.status_code == 200 else None

        if digest:
            push_mod = getattr(app.state, "push_module", None)
            if push_mod:
                summary = digest.get("summary", "Your daily A-GENTEE digest is ready.")
                body = summary[:120] + "..." if len(summary) > 120 else summary
                await push_mod.send_to_all_subscribers(
                    title="📋 Daily Digest — A-GENTEE",
                    body=body,
                    app=app,
                )
            logger.info("⏰ Daily digest generated and pushed")
        else:
            logger.info("⏰ Daily digest: no conversations to summarize")
    except Exception as e:
        logger.error(f"Daily digest job failed: {e}")


async def stale_reminder_job(app):
    """Check for stale insights via HTTP and push reminders."""
    import httpx

    try:
        port = os.environ.get("PORT", "8000")
        async with httpx.AsyncClient() as client:
            res = await client.get(f"http://127.0.0.1:{port}/api/v1/insights?actioned=false", timeout=30)
            data = res.json() if res.status_code == 200 else {}

        insights = data.get("insights", [])
        # Filter for insights older than 3 days
        from datetime import datetime, timezone, timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=3)
        stale = []
        for ins in insights:
            created = ins.get("created_at", "")
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if dt < cutoff:
                    stale.append(ins)
            except (ValueError, TypeError):
                continue

        if stale:
            push_mod = getattr(app.state, "push_module", None)
            if push_mod:
                count = len(stale)
                first = stale[0].get("content", "")[:80]
                await push_mod.send_to_all_subscribers(
                    title=f"⚡ {count} stale task{'s' if count > 1 else ''} need attention",
                    body=first + ("..." if len(first) >= 80 else ""),
                    app=app,
                )
            logger.info(f"⏰ Stale reminder: {len(stale)} tasks flagged")
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
