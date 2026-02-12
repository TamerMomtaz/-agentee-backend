"""
🛡️ A-GENTEE GuardTee — Service Health Monitor (Phase 2, System 5)
Monitors all A-GENTEE ecosystem services.
Pings each service, classifies health, stores results in Supabase.

Endpoints:
  GET /guard/check   — Run health check NOW on all services
  GET /guard/status   — Get latest status of all monitored services
  GET /guard/history  — Get health check history
"""

import os
import time
import logging
from typing import List, Dict, Optional

import httpx
from fastapi import APIRouter, Request

logger = logging.getLogger("agentee.api.guard")

router = APIRouter(prefix="/guard", tags=["GuardTee"])

# ── Services to Monitor ──

SERVICES = [
    {
        "name": "A-GENTEE Backend",
        "url": "https://agentee.up.railway.app/api/v1/health",
        "type": "json",
    },
    {
        "name": "A-GENTEE Frontend",
        "url": "https://agentee-frontend.vercel.app",
        "type": "http",
    },
    {
        "name": "Book of Tee Frontend",
        "url": "https://tamermomtaz.github.io/BookOfTee",
        "type": "http",
    },
    {
        "name": "Book of Tee Backend",
        "url": "https://web-production-f5f1e.up.railway.app",
        "type": "http",
    },
    {
        "name": "Supabase",
        "url": "https://pjaxznbcanpbsejrpljy.supabase.co/rest/v1/",
        "type": "http",
    },
]


# ── Health Check Logic ──

async def _check_service(service: Dict) -> Dict:
    """
    Ping a single service and classify its health.
    
    healthy  = 200 response in <2s
    degraded = 200 response in >=2s
    down     = non-200 or timeout or error
    """
    result = {
        "service_name": service["name"],
        "service_url": service["url"],
        "status": "down",
        "response_ms": None,
        "error": None,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            start = time.monotonic()
            
            # For Supabase, we need the apikey header
            headers = {}
            if "supabase" in service["url"]:
                supa_key = os.getenv("SUPABASE_KEY", "")
                if supa_key:
                    headers["apikey"] = supa_key

            resp = await client.get(service["url"], headers=headers)
            elapsed_ms = int((time.monotonic() - start) * 1000)
            result["response_ms"] = elapsed_ms

            if resp.status_code in (200, 301, 302, 304):
                result["status"] = "degraded" if elapsed_ms >= 2000 else "healthy"
            else:
                result["status"] = "down"
                result["error"] = f"HTTP {resp.status_code}"

    except httpx.TimeoutException:
        result["error"] = "Timeout (10s)"
    except httpx.ConnectError as e:
        result["error"] = f"Connection failed: {str(e)[:100]}"
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)[:100]}"

    return result


async def _store_check(request: Request, check: Dict) -> bool:
    """Store a health check result in Supabase."""
    memory = getattr(request.app.state, "memory", None)
    if not memory or not memory.client:
        return False
    try:
        resp = await memory.client.post(
            "/guardtee_checks",
            json={
                "service_name": check["service_name"],
                "service_url": check["service_url"],
                "status": check["status"],
                "response_ms": check["response_ms"],
                "error": check.get("error"),
            },
        )
        return resp.status_code in (200, 201)
    except Exception as e:
        logger.warning(f"Failed to store check: {e}")
        return False


async def _send_down_alerts(request: Request, down_services: List[Dict]):
    """If any service is down, trigger push notification."""
    if not down_services:
        return

    push_module = getattr(request.app.state, "push_module", None)
    if not push_module:
        logger.warning("🛡️ Service(s) down but push module not available")
        return

    names = ", ".join(s["service_name"] for s in down_services)
    try:
        await push_module.send_to_all_subscribers(
            title="🛡️ GuardTee Alert",
            body=f"Service(s) DOWN: {names}",
            request=request,
        )
        logger.info(f"🛡️ Push alert sent for: {names}")
    except Exception as e:
        logger.warning(f"Push alert failed: {e}")


# ── Endpoints ──

@router.get("/check")
async def run_health_check(request: Request):
    """
    Run health checks NOW on all monitored services.
    Stores results and triggers alerts for down services.
    """
    import asyncio

    # Check all services concurrently
    tasks = [_check_service(svc) for svc in SERVICES]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    checks = []
    down_services = []

    for r in results:
        if isinstance(r, Exception):
            logger.error(f"Check task error: {r}")
            continue
        checks.append(r)
        await _store_check(request, r)
        if r["status"] == "down":
            down_services.append(r)

    # Alert on down services
    await _send_down_alerts(request, down_services)

    # Summary
    healthy = sum(1 for c in checks if c["status"] == "healthy")
    degraded = sum(1 for c in checks if c["status"] == "degraded")
    down = sum(1 for c in checks if c["status"] == "down")

    return {
        "checked": len(checks),
        "summary": {
            "healthy": healthy,
            "degraded": degraded,
            "down": down,
        },
        "overall": "healthy" if down == 0 and degraded == 0 else ("degraded" if down == 0 else "critical"),
        "services": checks,
    }


@router.get("/status")
async def get_latest_status(request: Request):
    """
    Get the latest health status of each monitored service.
    Uses the most recent check per service from the database.
    """
    memory = getattr(request.app.state, "memory", None)
    if not memory or not memory.client:
        return {"error": "Memory not connected", "services": []}

    statuses = []
    for svc in SERVICES:
        try:
            resp = await memory.client.get(
                "/guardtee_checks",
                params={
                    "select": "service_name,status,response_ms,error,checked_at",
                    "service_name": f"eq.{svc['name']}",
                    "order": "checked_at.desc",
                    "limit": 1,
                },
            )
            data = resp.json() if resp.status_code == 200 else []
            if data:
                statuses.append(data[0])
            else:
                statuses.append({
                    "service_name": svc["name"],
                    "status": "unknown",
                    "response_ms": None,
                    "error": "No checks recorded yet",
                    "checked_at": None,
                })
        except Exception as e:
            statuses.append({
                "service_name": svc["name"],
                "status": "error",
                "error": str(e),
            })

    return {"services": statuses}


@router.get("/history")
async def get_check_history(
    request: Request,
    service: Optional[str] = None,
    limit: int = 50,
):
    """
    Get health check history. Optionally filter by service name.
    """
    memory = getattr(request.app.state, "memory", None)
    if not memory or not memory.client:
        return {"error": "Memory not connected", "history": []}

    try:
        params = {
            "select": "id,service_name,status,response_ms,error,checked_at",
            "order": "checked_at.desc",
            "limit": limit,
        }
        if service:
            params["service_name"] = f"eq.{service}"

        resp = await memory.client.get("/guardtee_checks", params=params)
        history = resp.json() if resp.status_code == 200 else []
        return {"history": history, "total": len(history)}
    except Exception as e:
        logger.error(f"History fetch error: {e}")
        return {"history": [], "error": str(e)}
