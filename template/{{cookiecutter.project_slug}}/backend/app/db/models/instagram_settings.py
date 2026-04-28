{%- if cookiecutter.enable_instagram %}
"""Instagram settings database model."""

import uuid

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class InstagramSettings(Base, TimestampMixin):
    """Instagram integration settings (singleton - one row)."""

    __tablename__ = "instagram_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    page_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    app_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    webhook_verify_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auto_reply: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<InstagramSettings(id={self.id}, page_id={self.page_id}, auto_reply={self.auto_reply})>"
{%- endif %}
