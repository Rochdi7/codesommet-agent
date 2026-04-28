{%- if cookiecutter.enable_instagram %}
"""Instagram settings repository."""

from typing import Any

{%- if cookiecutter.use_postgresql %}
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.instagram_settings import InstagramSettings


async def get(db: AsyncSession) -> InstagramSettings | None:
    """Get the singleton Instagram settings row."""
    result = await db.execute(select(InstagramSettings).limit(1))
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    *,
    page_id: str | None = None,
    page_access_token: str | None = None,
    app_secret: str | None = None,
    webhook_verify_token: str | None = None,
    auto_reply: bool = False,
) -> InstagramSettings:
    """Create Instagram settings."""
    settings = InstagramSettings(
        page_id=page_id,
        page_access_token=page_access_token,
        app_secret=app_secret,
        webhook_verify_token=webhook_verify_token,
        auto_reply=auto_reply,
    )
    db.add(settings)
    await db.flush()
    await db.refresh(settings)
    return settings


async def update(
    db: AsyncSession,
    *,
    db_settings: InstagramSettings,
    update_data: dict[str, Any],
) -> InstagramSettings:
    """Update Instagram settings."""
    for field, value in update_data.items():
        setattr(db_settings, field, value)
    db.add(db_settings)
    await db.flush()
    await db.refresh(db_settings)
    return db_settings
{%- elif cookiecutter.use_sqlite %}
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.instagram_settings import InstagramSettings


def get(db: Session) -> InstagramSettings | None:
    """Get the singleton Instagram settings row."""
    result = db.execute(select(InstagramSettings).limit(1))
    return result.scalar_one_or_none()


def create(
    db: Session,
    *,
    page_id: str | None = None,
    page_access_token: str | None = None,
    app_secret: str | None = None,
    webhook_verify_token: str | None = None,
    auto_reply: bool = False,
) -> InstagramSettings:
    """Create Instagram settings."""
    settings = InstagramSettings(
        page_id=page_id,
        page_access_token=page_access_token,
        app_secret=app_secret,
        webhook_verify_token=webhook_verify_token,
        auto_reply=auto_reply,
    )
    db.add(settings)
    db.flush()
    db.refresh(settings)
    return settings


def update(
    db: Session,
    *,
    db_settings: InstagramSettings,
    update_data: dict[str, Any],
) -> InstagramSettings:
    """Update Instagram settings."""
    for field, value in update_data.items():
        setattr(db_settings, field, value)
    db.add(db_settings)
    db.flush()
    db.refresh(db_settings)
    return db_settings
{%- endif %}
{%- endif %}
