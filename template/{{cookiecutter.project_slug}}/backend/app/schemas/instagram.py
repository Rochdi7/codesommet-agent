{%- if cookiecutter.enable_instagram %}
"""Instagram settings schemas."""

from pydantic import Field

from app.schemas.base import BaseSchema, BaseResponse, TimestampSchema


class InstagramSettingsUpdate(BaseSchema):
    """Schema for saving Instagram settings from the dashboard form."""

    page_id: str | None = Field(default=None, max_length=255)
    page_access_token: str | None = Field(default=None)
    app_secret: str | None = Field(default=None, max_length=255)
    webhook_verify_token: str | None = Field(default=None, max_length=255)
    auto_reply: bool | None = None


class InstagramSettingsRead(BaseSchema, TimestampSchema):
    """Schema for reading Instagram settings."""

    id: str
    page_id: str | None = None
    page_access_token_set: bool = False
    app_secret_set: bool = False
    webhook_verify_token: str | None = None
    auto_reply: bool = False


class InstagramTestLog(BaseSchema):
    """Single test check result."""

    field: str
    status: str  # "ok", "error", "skip"
    message: str
    detail: str | None = None


class InstagramTestResult(BaseResponse):
    """Full test/debug result with per-field logs."""

    logs: list[InstagramTestLog] = []
    page_name: str | None = None
    instagram_business_account_id: str | None = None
{%- endif %}
