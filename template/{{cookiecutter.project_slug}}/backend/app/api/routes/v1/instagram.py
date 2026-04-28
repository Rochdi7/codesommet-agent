{%- if cookiecutter.enable_instagram %}
"""Instagram settings and webhook routes."""

import hashlib
import hmac
import json
import logging
from typing import Any

from fastapi import APIRouter, Query, Request, status
from fastapi.responses import PlainTextResponse

from app.api.deps import CurrentAdmin, DBSession, InstagramSvc
from app.core.exceptions import AuthenticationError, BadRequestError
from app.schemas.instagram import InstagramSettingsRead, InstagramSettingsUpdate, InstagramTestResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/instagram")


# === Settings endpoints (admin only) ===


@router.get("/settings", response_model=InstagramSettingsRead)
{%- if cookiecutter.use_postgresql %}
async def get_instagram_settings(service: InstagramSvc, user: CurrentAdmin) -> Any:
    """Get current Instagram integration settings."""
    settings = await service.get_settings()
{%- elif cookiecutter.use_sqlite %}
def get_instagram_settings(service: InstagramSvc, user: CurrentAdmin) -> Any:
    """Get current Instagram integration settings."""
    settings = service.get_settings()
{%- endif %}
    if not settings:
        return InstagramSettingsRead(
            id="",
            page_id=None,
            page_access_token_set=False,
            app_secret_set=False,
            webhook_verify_token=None,
            auto_reply=False,
            created_at="1970-01-01T00:00:00+00:00",
            updated_at=None,
        )
    return InstagramSettingsRead(
        id=settings.id,
        page_id=settings.page_id,
        page_access_token_set=bool(settings.page_access_token),
        app_secret_set=bool(settings.app_secret),
        webhook_verify_token=settings.webhook_verify_token,
        auto_reply=settings.auto_reply,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


@router.put("/settings", response_model=InstagramSettingsRead)
{%- if cookiecutter.use_postgresql %}
async def save_instagram_settings(
    data: InstagramSettingsUpdate, service: InstagramSvc, user: CurrentAdmin
) -> Any:
    """Save Instagram integration settings (create or update)."""
    settings = await service.save_settings(data)
{%- elif cookiecutter.use_sqlite %}
def save_instagram_settings(
    data: InstagramSettingsUpdate, service: InstagramSvc, user: CurrentAdmin
) -> Any:
    """Save Instagram integration settings (create or update)."""
    settings = service.save_settings(data)
{%- endif %}
    return InstagramSettingsRead(
        id=settings.id,
        page_id=settings.page_id,
        page_access_token_set=bool(settings.page_access_token),
        app_secret_set=bool(settings.app_secret),
        webhook_verify_token=settings.webhook_verify_token,
        auto_reply=settings.auto_reply,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


@router.post("/test", response_model=InstagramTestResult)
{%- if cookiecutter.use_postgresql %}
async def test_instagram_connection(service: InstagramSvc, user: CurrentAdmin) -> Any:
    """Test Instagram credentials against Meta Graph API."""
    result = await service.test_connection()
{%- elif cookiecutter.use_sqlite %}
def test_instagram_connection(service: InstagramSvc, user: CurrentAdmin) -> Any:
    """Test Instagram credentials against Meta Graph API."""
    result = service.test_connection()
{%- endif %}
    return InstagramTestResult(**result)


# === Webhook endpoints (no auth - called by Meta) ===


@router.get("/webhook")
{%- if cookiecutter.use_postgresql %}
async def verify_webhook(
    db: DBSession,
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
) -> PlainTextResponse:
    """Meta webhook verification (GET)."""
    from app.services.instagram import InstagramService

    service = InstagramService(db)
    stored_token = await service.get_verify_token()
{%- elif cookiecutter.use_sqlite %}
def verify_webhook(
    db: DBSession,
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
) -> PlainTextResponse:
    """Meta webhook verification (GET)."""
    from app.services.instagram import InstagramService

    service = InstagramService(db)
    stored_token = service.get_verify_token()
{%- endif %}

    if not stored_token:
        raise BadRequestError(
            message="Instagram webhook not configured",
            details={"hint": "Save Instagram settings first"},
        )

    if hub_mode != "subscribe":
        raise BadRequestError(message="Invalid hub.mode", details={"hub_mode": hub_mode})

    if hub_verify_token != stored_token:
        raise AuthenticationError(message="Invalid verify token")

    logger.info("Instagram webhook verified successfully")
    return PlainTextResponse(content=hub_challenge)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def receive_webhook(request: Request) -> dict[str, str]:
    """Receive Instagram webhook events (POST)."""
    body = await request.body()

{%- if cookiecutter.use_postgresql %}
    from app.db.session import get_db_context
    from app.services.instagram import InstagramService

    async with get_db_context() as db:
        service = InstagramService(db)
        settings = await service.get_settings()

        if settings and settings.app_secret:
            signature_header = request.headers.get("x-hub-signature-256", "")
            expected = "sha256=" + hmac.new(
                settings.app_secret.encode(), body, hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(expected, signature_header):
                logger.warning("Instagram webhook signature verification failed")
                raise AuthenticationError(message="Invalid webhook signature")
{%- elif cookiecutter.use_sqlite %}
    from app.db.session import SessionLocal
    from app.services.instagram import InstagramService

    with SessionLocal() as db:
        service = InstagramService(db)
        settings = service.get_settings()

        if settings and settings.app_secret:
            signature_header = request.headers.get("x-hub-signature-256", "")
            expected = "sha256=" + hmac.new(
                settings.app_secret.encode(), body, hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(expected, signature_header):
                logger.warning("Instagram webhook signature verification failed")
                raise AuthenticationError(message="Invalid webhook signature")
{%- endif %}

    payload = json.loads(body)
    logger.info("Instagram webhook received: %s", payload.get("object", "unknown"))

    for entry in payload.get("entry", []):
        for msg_event in entry.get("messaging", []):
            sender = msg_event.get("sender", {}).get("id", "unknown")
            message = msg_event.get("message", {})
            text = message.get("text", "")
            mid = message.get("mid", "")
            logger.info("Instagram DM from %s: %s (mid: %s)", sender, text, mid)

    return {"status": "received"}
{%- endif %}
