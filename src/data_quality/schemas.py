
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WeatherObservation(BaseModel):
    """Validated weather observation for GeoSentinel AI."""

    model_config = ConfigDict(extra="forbid")

    location_id: str = Field(min_length=1, max_length=100)

    observed_at: datetime

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    precipitation_mm: float = Field(ge=0, allow_inf_nan=False)

    source_id: str = Field(min_length=1, max_length=200)

    data_origin: Literal["real", "synthetic"]

    @field_validator("location_id", "source_id")
    @classmethod
    def validate_identifiers(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Identifier must not be empty.")
        return value

    @field_validator("observed_at")
    @classmethod
    def require_timezone_aware_timestamp(
        cls, value: datetime
    ) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "observed_at must include a timezone."
            )
        return value
