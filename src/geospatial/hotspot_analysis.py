
import json
from collections import Counter
from pathlib import Path
import os

INPUT_FILE = Path("data/processed/hyderabad_flooding_points.geojson")
OUTPUT_FILE = Path("data/processed/hyderabad_flooding_hotspots.geojson")

# Grid size in degrees. This is an exploratory grid, not an exact
# ground-distance measurement.
GRID_SIZE = float(os.getenv("GEOSENTINEL_GRID_SIZE", "0.02"))
if not 0 < GRID_SIZE <= 1:
    raise ValueError("GEOSENTINEL_GRID_SIZE must be greater than 0 and at most 1.")


def load_flooding_points(path: Path) -> list[dict]:
    """Load and validate mapped flooding Point features."""
    with path.open("r", encoding="utf-8") as file:
        geojson = json.load(file)

    if geojson.get("type") != "FeatureCollection":
        raise ValueError("Input must be a GeoJSON FeatureCollection.")

    points = []

    for feature in geojson.get("features", []):
        geometry = feature.get("geometry") or {}

        if geometry.get("type") != "Point":
            continue

        coordinates = geometry.get("coordinates", [])
        if len(coordinates) < 2:
            continue

        longitude, latitude = coordinates[:2]

        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            continue

        points.append(
            {
                "longitude": longitude,
                "latitude": latitude,
                "name": feature.get("properties", {}).get(
                    "name", "Unnamed location"
                ),
            }
        )

    return points


def build_hotspots(points: list[dict]) -> dict:
    """Count mapped flooding locations in each grid cell."""
    counts = Counter()
    cell_bounds = {}

    for point in points:
        longitude = point["longitude"]
        latitude = point["latitude"]

        cell_x = int(longitude // GRID_SIZE)
        cell_y = int(latitude // GRID_SIZE)
        key = (cell_x, cell_y)

        counts[key] += 1

        west = cell_x * GRID_SIZE
        south = cell_y * GRID_SIZE
        cell_bounds[key] = [
            west,
            south,
            west + GRID_SIZE,
            south + GRID_SIZE,
        ]

    features = []

    for (cell_x, cell_y), count in sorted(
        counts.items(), key=lambda item: (-item[1], item[0])
    ):
        west, south, east, north = cell_bounds[(cell_x, cell_y)]

        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [west, south],
                        [east, south],
                        [east, north],
                        [west, north],
                        [west, south],
                    ]],
                },
                "properties": {
                    "grid_id": f"{cell_x}_{cell_y}",
                    "mapped_location_count": count,
                    "record_type": "mapped_location_concentration",
                    "data_origin": "derived_from_real_location_inventory",
                    "is_flooding_prediction": False,
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def main() -> None:
    points = load_flooding_points(INPUT_FILE)

    if not points:
        raise ValueError("No valid flooding-location points were found.")

    hotspots = build_hotspots(points)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(hotspots, file, indent=2)

    print(f"Mapped points analyzed: {len(points)}")
    print(f"Grid cells with mapped locations: {len(hotspots['features'])}")
    print(f"Output saved: {OUTPUT_FILE}")
    print("Note: These counts are not live status or flood predictions.")


if __name__ == "__main__":
    main()
