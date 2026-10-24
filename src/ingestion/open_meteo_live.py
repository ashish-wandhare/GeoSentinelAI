
"""Fetch current and recent hourly weather for GeoSentinel AI."""

from datetime import datetime, timezone
import json
from pathlib import Path

import httpx

from src.config import settings
from src.ingestion.open_meteo_history import (
    HYDERABAD_LATITUDE,
    HYDERABAD_LONGITUDE,
)

API_URL = "https://api.open-meteo.com/v1/forecast"
OUTPUT_FILE = settings.data_dir / "raw" / "hyderabad_live_weather.json"


def fetch_weather_for_coordinates(
    latitude: float,
    longitude: float,
) -> dict:
    """Fetch weather for validated geographic coordinates."""

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,precipitation,rain",
        "hourly": "precipitation",
        "past_hours": 24,
        "forecast_hours": 1,
        "timezone": "GMT",
        "precipitation_unit": "mm",
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(API_URL, params=params)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPError as exc:
        raise RuntimeError(
            f"Unable to retrieve weather from Open-Meteo: {exc}"
        ) from exc

    if not isinstance(payload, dict) or payload.get("error"):
        raise ValueError("Open-Meteo returned an invalid weather response.")

    current = payload.get("current")
    if not isinstance(current, dict):
        raise ValueError("Current weather data is missing.")

    for field in ("time", "precipitation", "rain"):
        if current.get(field) is None:
            raise ValueError(f"Current weather field is missing: {field}")

    return {
        "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_status": "live_weather_observation",
        "source": "Open-Meteo",
        "location": {
            "latitude": payload.get("latitude", latitude),
            "longitude": payload.get("longitude", longitude),
            "description": "Weather for the supplied coordinates",
        },
        "current": current,
        "hourly": payload.get("hourly", {}),
        "waterlogging_confirmed": False,
        "is_flooding_prediction": False,
    }


def fetch_live_weather() -> dict:
    """Fetch weather for the existing Hyderabad reference point."""

    data = fetch_weather_for_coordinates(
        HYDERABAD_LATITUDE,
        HYDERABAD_LONGITUDE,
    )

    data["location"]["description"] = (
        "Hyderabad reference point; not street-level"
    )
    return data


def save_live_weather(
    data: dict,
    output_file: Path = OUTPUT_FILE,
) -> Path:
    """Save the latest live response separately from historical data."""

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_file


def main() -> None:
    data = fetch_live_weather()
    output = save_live_weather(data)

    print(f"Weather observation time (UTC): {data['current']['time']}")
    print(f"Current rainfall: {data['current']['precipitation']} mm")
    print(f"Live weather saved to: {output.resolve()}")
    print("Note: rainfall observations do not confirm waterlogging.")


if __name__ == "__main__":
    main()
