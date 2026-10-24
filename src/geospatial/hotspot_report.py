
import json
from datetime import datetime, timezone
from pathlib import Path

from src.geospatial.hotspot_analysis import GRID_SIZE

POINTS_FILE = Path("data/processed/hyderabad_flooding_points.geojson")
HOTSPOTS_FILE = Path("data/processed/hyderabad_flooding_hotspots.geojson")
REPORT_FILE = Path("data/processed/hyderabad_hotspot_report.json")


def read_geojson(path: Path) -> dict:
    """Read a GeoJSON file and validate its top-level type."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") != "FeatureCollection":
        raise ValueError(f"{path} must contain a GeoJSON FeatureCollection.")

    if not isinstance(data.get("features"), list):
        raise ValueError(f"{path} must contain a features list.")

    return data


def build_report(points_geojson: dict, hotspots_geojson: dict) -> dict:
    """Build a reproducible summary of mapped-location concentration."""
    points = [
        feature
        for feature in points_geojson["features"]
        if feature.get("geometry", {}).get("type") == "Point"
        and len(feature["geometry"].get("coordinates", [])) >= 2
    ]

    hotspots = [
        feature
        for feature in hotspots_geojson["features"]
        if feature.get("geometry", {}).get("type") == "Polygon"
    ]

    coordinates = [
        feature["geometry"]["coordinates"][:2]
        for feature in points
    ]

    counts = [
        feature.get("properties", {}).get("mapped_location_count", 0)
        for feature in hotspots
    ]

    if any(not isinstance(count, int) or count < 0 for count in counts):
        raise ValueError("Hotspot counts must be non-negative integers.")

    total_counted = sum(counts)

    if total_counted != len(points):
        raise ValueError(
            "Hotspot count total does not match the number of mapped points: "
            f"{total_counted} versus {len(points)}."
        )

    if coordinates:
        longitudes = [coordinate[0] for coordinate in coordinates]
        latitudes = [coordinate[1] for coordinate in coordinates]
        bounds = {
            "west": min(longitudes),
            "south": min(latitudes),
            "east": max(longitudes),
            "north": max(latitudes),
        }
    else:
        bounds = None

    return {
        "report_generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_type": "mapped_location_concentration",
        "grid_size_degrees": GRID_SIZE,
        "summary": {
            "mapped_point_count": len(points),
            "occupied_grid_cell_count": len(hotspots),
            "total_locations_counted_in_grid": total_counted,
            "maximum_locations_per_cell": max(counts, default=0),
            "cells_with_multiple_locations": sum(
                count >= 2 for count in counts
            ),
        },
        "geographic_bounds_wgs84": bounds,
        "data_provenance": {
            "point_dataset": str(POINTS_FILE),
            "hotspot_dataset": str(HOTSPOTS_FILE),
            "point_record_type": "mapped_flooding_location",
            "point_data_origin": "real",
            "independently_verified": False,
            "occurrence_timestamps_available": False,
            "severity_labels_available": False,
        },
        "limitations": [
            "Mapped locations are not timestamped flooding incidents.",
            "Locations have not been independently verified.",
            "Grid counts measure location concentration, not flood probability.",
            "This analysis does not provide live status or predict future flooding.",
            "Results depend on the selected grid resolution.",
        ],
    }


def main() -> None:
    points_geojson = read_geojson(POINTS_FILE)
    hotspots_geojson = read_geojson(HOTSPOTS_FILE)

    report = build_report(points_geojson, hotspots_geojson)

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_FILE.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print(f"Mapped points: {report['summary']['mapped_point_count']}")
    print(
        "Occupied grid cells: "
        f"{report['summary']['occupied_grid_cell_count']}"
    )
    print(
        "Maximum locations per cell: "
        f"{report['summary']['maximum_locations_per_cell']}"
    )
    print(f"Report saved: {REPORT_FILE}")
    print("This report describes mapped-location concentration, not flood risk.")


if __name__ == "__main__":
    main()
