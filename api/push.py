"""
📢 A-GENTEE Push Notifications (Phase 2, System 3)
Web Push via VAPID for proactive alerts.

Endpoints:
  GET  /push/vapid     — Get VAPID public key for frontend
  POST /push/subscribe — Store push subscription from frontend
  POST /push/send      — Send a push notification (admin)

Notification triggers (called from other modules):
  1. Service down (GuardTee)
  2. Daily digest ready
  3. Stale task reminder (insights unactioned >3 days)
  4. Proactive suggestion (cross-project connection)
"""

import os
import json
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("agentee.api.push")

router = APIRouter(prefix="/push", tags=["Push Notifications"])


# ── Request Models ──

class PushSubscription(BaseModel):
    """Web Push subscription from the frontend service worker."""
    endpoint: str
    p256dh: str
    auth: str
    user_agent: Optional[str] = None


class PushMessage(BaseModel):
    """Manual push notification (admin use)."""
    title: str = "🌊 A-GENTEE"
    body: str
    url: Optional[str] = None  # Click action URL
    tag: Optional[str] = None  # Notification grouping tag


# ── VAPID Config ──

def _get_vapid_keys():
    """Get VAPID keys from environment."""
    return {
        "private_key": os.getenv("VAPID_PRIVATE_KEY", ""),
        "public_key": os.getenv("VAPID_PUBLIC_KEY", ""),
        "claims_email": os.getenv("VAPID_CLAIMS_EMAIL", "tee@devoneers.com"),
    }


# ── Endpoints ──

@router.get("/vapid")
async def get_vapid_public_key():
    """
    Get the VAPID public key for frontend to create push subscriptions.
    Frontend uses this in serviceWorkerRegistration.pushManager.subscribe().
    """
    keys = _get_vapid_keys()
    if not keys["public_key"]:
        raise HTTPException(
            status_code=503,
            detail="VAPID keys not configured. Set VAPID_PUBLIC_KEY in environment.",
        )
    return {"public_key": keys["public_key"]}


@router.post("/subscribe")
async def subscribe(sub: PushSubscription, request: Request):
    """
    Store a push subscription from the frontend.
    Called after the user grants notification permission.
    """
    memory = getattr(request.app.state, "memory", None)
    if not memory or not memory.client:
        raise HTTPException(status_code=503, detail="Memory not connected")

    try:
        # Upsert — if endpoint already exists, update keys
        # First try to delete existing (Supabase REST doesn't have native upsert easily)
        await memory.client.delete(
            "/push_subscriptions",
            params={"endpoint": f"eq.{sub.endpoint}"},
        )

        resp = await memory.client.post(
            "/push_subscriptions",
            json={
                "endpoint": sub.endpoint,
                "p256dh": sub.p256dh,
                "auth": sub.auth,
                "user_agent": sub.user_agent,
            },
        )

        if resp.status_code in (200, 201):
            logger.info(f"📢 Push subscription stored: {sub.endpoint[:60]}...")
            return {"subscribed": True}
        else:
            logger.warning(f"Subscribe store: {resp.status_code} — {resp.text[:200]}")
            raise HTTPException(status_code=500, detail="Failed to store subscription")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscribe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
async def send_notification(msg: PushMessage, request: Request):
    """
    Send a push notification to all subscribers (admin endpoint).
    In production, add API key auth here.
    """
    count = await send_to_all_subscribers(
        title=msg.title,
        body=msg.body,
        url=msg.url,
        tag=msg.tag,
        request=request,
    )
    return {"sent": count, "title": msg.title}


# ── Push Sending Logic ──

async def send_to_all_subscribers(
    title: str,
    body: str,
    request: Request,
    url: Optional[str] = None,
    tag: Optional[str] = None,
) -> int:
    """
    Send a web push notification to ALL stored subscribers.
    Returns number of successfully sent notifications.
    """
    memory = getattr(request.app.state, "memory", None)
    if not memory or not memory.client:
        logger.warning("Push: memory not available")
        return 0

    keys = _get_vapid_keys()
    if not keys["private_key"] or not keys["public_key"]:
        logger.warning("Push: VAPID keys not configured")
        return 0

    # Get all subscriptions
    try:
        resp = await memory.client.get(
            "/push_subscriptions",
            params={"select": "id,endpoint,p256dh,auth"},
        )
        subscriptions = resp.json() if resp.status_code == 200 else []
    except Exception as e:
        logger.error(f"Push: failed to get subscriptions: {e}")
        return 0

    if not subscriptions:
        logger.info("Push: no subscribers")
        return 0

    # Build notification payload
    payload = json.dumps({
        "title": title,
        "body": body,
        "icon": "/icon-192.png",
        "badge": "/badge-72.png",
        "url": url or "https://agentee-frontend.vercel.app",
        "tag": tag or "agentee-notification",
    })

    sent = 0
    expired = []

    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        logger.error("Push: pywebpush not installed")
        return 0

    for sub in subscriptions:
        subscription_info = {
            "endpoint": sub["endpoint"],
            "keys": {
                "p256dh": sub["p256dh"],
                "auth": sub["auth"],
            },
        }

        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=keys["private_key"],
                vapid_claims={"sub": f"mailto:{keys['claims_email']}"},
            )
            sent += 1
        except WebPushException as e:
            status_code = getattr(e, "response", None)
            status = getattr(status_code, "status_code", 0) if status_code else 0
            if status in (404, 410):
                # Subscription expired — mark for cleanup
                expired.append(sub["id"])
                logger.info(f"Push: subscription expired, cleaning up")
            else:
                logger.warning(f"Push failed: {e}")
        except Exception as e:
            logger.warning(f"Push error: {e}")

    # Clean up expired subscriptions
    for sub_id in expired:
        try:
            await memory.client.delete(
                "/push_subscriptions",
                params={"id": f"eq.{sub_id}"},
            )
        except Exception:
            pass

    logger.info(f"📢 Push sent: {sent}/{len(subscriptions)} (expired: {len(expired)})")
    return sent
