
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WaterloggingIncident(BaseModel):
    """Validated waterlogging incident record for GeoSentinel AI."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(min_length=1, max_length=100)
    location_id: str = Field(min_length=1, max_length=100)

    # When the waterlogging incident occurred, not when it was downloaded.
    occurred_at: datetime

    # When the incident was reported or entered into the system.
    reported_at: datetime

    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)

    source_id: str = Field(min_length=1, max_length=200)

    verification_status: Literal[
        "unverified",
        "verified",
        "rejected",
    ] = "unverified"

    severity: Literal[
        "low",
        "moderate",
        "high",
        "critical",
    ] | None = None

    data_origin: Literal["real", "synthetic"]

    source_reference: str | None = Field(
        default=None,
        max_length=500,
    )

    @field_validator(
        "incident_id",
        "location_id",
        "source_id",
    )
    @classmethod
    def validate_identifiers(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Identifier must not be empty.")
        return value

    @field_validator("occurred_at", "reported_at")
    @classmethod
    def require_timezone_aware_timestamp(
        cls,
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "Timestamps must include a timezone."
            )
        return value
