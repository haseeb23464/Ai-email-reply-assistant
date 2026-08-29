from typing import Literal

from pydantic import BaseModel, Field, field_validator


class GenerateReplyRequest(BaseModel):
    """Request body for POST /generate-reply."""

    email_content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The email content to generate a reply for (1–5000 characters)",
    )
    tone: Literal["Professional", "Friendly", "Short and Concise"] = Field(
        ...,
        description="The desired tone: Professional, Friendly, or Short and Concise",
    )

    @field_validator("email_content", mode="before")
    @classmethod
    def reject_whitespace_only(cls, value: str) -> str:
        """Strip leading/trailing whitespace, then reject if nothing remains.

        Safeguard: treats whitespace-only input identically to empty input so
        both hit the same user-facing error message.
        """
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                # ── Safeguard: clear message for empty / whitespace-only input.
                raise ValueError(
                    "Please enter an email before generating a reply."
                )
            return stripped
        return value

    @field_validator("email_content", mode="after")
    @classmethod
    def check_max_length_friendly(cls, value: str) -> str:
        """Provide a human-readable message when the email is too long.

        Safeguard: Pydantic's built-in max_length error is technical; this
        validator fires after stripping and gives a friendlier message.
        """
        if len(value) > 5000:
            raise ValueError(
                "Email content is too long. Please limit it to 5,000 characters."
            )
        return value


class GenerateReplyResponse(BaseModel):
    """Response body for POST /generate-reply."""

    reply: str = Field(
        ...,
        description="The AI-generated email reply",
    )
    tone: str = Field(
        ...,
        description="The tone that was used to generate the reply",
    )
