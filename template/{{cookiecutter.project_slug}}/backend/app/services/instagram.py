{%- if cookiecutter.enable_instagram %}
"""Instagram settings service."""

import hashlib
import hmac
import logging
from typing import Any

import httpx
{%- if cookiecutter.use_postgresql %}
from sqlalchemy.ext.asyncio import AsyncSession
{%- elif cookiecutter.use_sqlite %}
from sqlalchemy.orm import Session
{%- endif %}

from app.db.models.instagram_settings import InstagramSettings
from app.repositories import instagram_settings_repo
from app.schemas.instagram import InstagramSettingsUpdate, InstagramTestLog

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


class InstagramService:
    """Service for Instagram settings management."""

{%- if cookiecutter.use_postgresql %}
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_settings(self) -> InstagramSettings | None:
        """Get current Instagram settings."""
        return await instagram_settings_repo.get(self.db)

    async def save_settings(self, data: InstagramSettingsUpdate) -> InstagramSettings:
        """Create or update Instagram settings (upsert)."""
        existing = await instagram_settings_repo.get(self.db)
        update_data = data.model_dump(exclude_unset=True)

        if existing:
            return await instagram_settings_repo.update(
                self.db, db_settings=existing, update_data=update_data
            )

        return await instagram_settings_repo.create(self.db, **update_data)

    async def get_verify_token(self) -> str | None:
        """Get the webhook verify token for Meta verification."""
        settings = await instagram_settings_repo.get(self.db)
        if settings:
            return settings.webhook_verify_token
        return None

    async def test_connection(self) -> dict[str, Any]:
        """Test all Instagram credentials against Meta Graph API."""
        settings = await self.get_settings()
        return _test_connection_impl(settings)
{%- elif cookiecutter.use_sqlite %}
    def __init__(self, db: Session):
        self.db = db

    def get_settings(self) -> InstagramSettings | None:
        """Get current Instagram settings."""
        return instagram_settings_repo.get(self.db)

    def save_settings(self, data: InstagramSettingsUpdate) -> InstagramSettings:
        """Create or update Instagram settings (upsert)."""
        existing = instagram_settings_repo.get(self.db)
        update_data = data.model_dump(exclude_unset=True)

        if existing:
            return instagram_settings_repo.update(
                self.db, db_settings=existing, update_data=update_data
            )

        return instagram_settings_repo.create(self.db, **update_data)

    def get_verify_token(self) -> str | None:
        """Get the webhook verify token for Meta verification."""
        settings = instagram_settings_repo.get(self.db)
        if settings:
            return settings.webhook_verify_token
        return None

    def test_connection(self) -> dict[str, Any]:
        """Test all Instagram credentials against Meta Graph API."""
        settings = self.get_settings()
        return _test_connection_impl(settings)
{%- endif %}


def _test_connection_impl(settings: InstagramSettings | None) -> dict[str, Any]:
    """Test Instagram credentials (shared logic for sync/async)."""
    logs: list[InstagramTestLog] = []
    all_ok = True
    page_name: str | None = None
    ig_account_id: str | None = None

    if not settings:
        logs.append(InstagramTestLog(
            field="settings",
            status="error",
            message="No Instagram settings saved yet",
            detail="Go to Instagram Settings and click Save first.",
        ))
        return {"success": False, "logs": logs, "page_name": None, "instagram_business_account_id": None}

    # Check Page ID
    if not settings.page_id:
        logs.append(InstagramTestLog(field="page_id", status="error", message="Page ID is empty"))
        all_ok = False
    else:
        logs.append(InstagramTestLog(field="page_id", status="ok", message=f"Page ID is set: {settings.page_id}"))

    # Check Page Access Token
    if not settings.page_access_token:
        logs.append(InstagramTestLog(field="page_access_token", status="error", message="Page Access Token is empty"))
        all_ok = False
    else:
        logs.append(InstagramTestLog(
            field="page_access_token", status="ok",
            message=f"Page Access Token is set ({len(settings.page_access_token)} chars)",
        ))

    # Check App Secret
    if not settings.app_secret:
        logs.append(InstagramTestLog(field="app_secret", status="error", message="App Secret is empty"))
        all_ok = False
    else:
        logs.append(InstagramTestLog(
            field="app_secret", status="ok",
            message=f"App Secret is set ({len(settings.app_secret)} chars)",
        ))

    # Check Webhook Verify Token
    if not settings.webhook_verify_token:
        logs.append(InstagramTestLog(field="webhook_verify_token", status="error", message="Webhook Verify Token is empty"))
        all_ok = False
    else:
        logs.append(InstagramTestLog(
            field="webhook_verify_token", status="ok",
            message=f"Webhook Verify Token is set: {settings.webhook_verify_token}",
        ))

    # Validate token + page_id against Meta Graph API
    if settings.page_access_token and settings.page_id:
        try:
            with httpx.Client(timeout=10.0) as client:
                me_resp = client.get(
                    f"{GRAPH_API_BASE}/me",
                    params={"access_token": settings.page_access_token, "fields": "id,name"},
                )
                me_data = me_resp.json()

                if "error" in me_data:
                    err = me_data["error"]
                    logs.append(InstagramTestLog(
                        field="page_access_token", status="error",
                        message=f"Token invalid: {err.get('message', 'Unknown error')}",
                        detail=f"Error type: {err.get('type')}, code: {err.get('code')}.",
                    ))
                    all_ok = False
                else:
                    token_page_id = me_data.get("id")
                    page_name = me_data.get("name")
                    logs.append(InstagramTestLog(
                        field="page_access_token", status="ok",
                        message=f"Token is valid! Page: {page_name} (ID: {token_page_id})",
                    ))

                    if token_page_id != settings.page_id:
                        logs.append(InstagramTestLog(
                            field="page_id", status="error",
                            message=f"Page ID mismatch! Token belongs to {token_page_id}, entered {settings.page_id}",
                        ))
                        all_ok = False

                # Check Instagram Business Account
                ig_resp = client.get(
                    f"{GRAPH_API_BASE}/{settings.page_id}",
                    params={"access_token": settings.page_access_token, "fields": "instagram_business_account,name"},
                )
                ig_data = ig_resp.json()

                if "error" in ig_data:
                    logs.append(InstagramTestLog(
                        field="instagram_business_account", status="error",
                        message=f"Cannot fetch page info: {ig_data['error'].get('message', 'Unknown')}",
                    ))
                    all_ok = False
                elif "instagram_business_account" not in ig_data:
                    logs.append(InstagramTestLog(
                        field="instagram_business_account", status="error",
                        message="No Instagram Business Account linked to this page",
                    ))
                    all_ok = False
                else:
                    ig_account_id = ig_data["instagram_business_account"]["id"]
                    logs.append(InstagramTestLog(
                        field="instagram_business_account", status="ok",
                        message=f"Instagram Business Account found: {ig_account_id}",
                    ))

        except httpx.ConnectError as exc:
            logs.append(InstagramTestLog(field="network", status="error", message=f"Cannot connect to Meta: {exc}"))
            all_ok = False
        except httpx.TimeoutException as exc:
            logs.append(InstagramTestLog(field="network", status="error", message=f"Meta API timed out: {exc}"))
            all_ok = False

    # Test App Secret HMAC
    if settings.app_secret:
        try:
            test_body = b'{"test":"hmac_check"}'
            signature = "sha256=" + hmac.new(
                settings.app_secret.encode(), test_body, hashlib.sha256
            ).hexdigest()
            logs.append(InstagramTestLog(
                field="app_secret", status="ok",
                message="App Secret HMAC generation works",
                detail=f"Test signature: {signature[:30]}...",
            ))
        except Exception as exc:
            logs.append(InstagramTestLog(field="app_secret", status="error", message=f"HMAC failed: {exc}"))
            all_ok = False

    return {
        "success": all_ok,
        "logs": logs,
        "page_name": page_name,
        "instagram_business_account_id": ig_account_id,
    }
{%- endif %}
