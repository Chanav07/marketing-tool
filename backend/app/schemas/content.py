from pydantic import BaseModel, Field, field_validator


class ContentGenerateIn(BaseModel):
    """Request to generate a piece of marketing content for a brand."""

    form: str  # 'long' | 'short'
    content_format: str = Field(min_length=1, max_length=80)
    platform: str = Field(min_length=1, max_length=80)

    @field_validator("form")
    @classmethod
    def valid_form(cls, v: str) -> str:
        if v not in ("long", "short"):
            raise ValueError("form must be 'long' or 'short'")
        return v

    @field_validator("content_format", "platform")
    @classmethod
    def strip_nonempty(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("must not be empty")
        return v


class ContentGenerateOut(BaseModel):
    script: str
