
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

SOURCE_FILE = Path("data/raw/hyderabad_flooding_points.kml")
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "hyderabad_flooding_points.geojson"
MANIFEST_FILE = OUTPUT_DIR / "hyderabad_flooding_points_manifest.json"

SOURCE_PAGE = (
    "https://data.opencity.in/dataset/flooding-locations-in-hyderabad"
)
NS = {"kml": "http://www.opengis.net/kml/2.2"}


def slugify(value: str) -> str:
    """Create a readable, deterministic identifier component."""
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    return value.strip("-") or "unnamed"


def convert_kml(source_file: Path) -> dict:
    """Convert named KML point placemarks to a GeoJSON FeatureCollection."""
    if not source_file.exists():
        raise FileNotFoundError(f"KML file not found: {source_file}")

    root = ET.parse(source_file).getroot()
    placemarks = root.findall(".//kml:Placemark", NS)

    features = []
    seen_coordinates = set()
    seen_names = set()
    duplicate_coordinate_count = 0
    duplicate_name_count = 0

    for index, placemark in enumerate(placemarks, start=1):
        name = (
            placemark.findtext("kml:name", default="", namespaces=NS).strip()
        )

        point = placemark.find(".//kml:Point", NS)
        if point is None:
            raise ValueError(
                f"Placemark {index} is not a Point geometry."
            )

        coordinate_text = point.findtext(
            "kml:coordinates", default="", namespaces=NS
        ).strip()

        if not coordinate_text:
            raise ValueError(
                f"Placemark {index} has no coordinates."
            )

        parts = coordinate_text.split()[0].split(",")
        if len(parts) < 2:
            raise ValueError(
                f"Invalid coordinate format in placemark {index}."
            )

        longitude, latitude = float(parts[0]), float(parts[1])

        if not (-180 <= longitude <= 180):
            raise ValueError(f"Longitude out of range in placemark {index}.")
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Latitude out of range in placemark {index}.")

        coordinate_key = (round(longitude, 8), round(latitude, 8))
        normalized_name = name.casefold()

        if coordinate_key in seen_coordinates:
            duplicate_coordinate_count += 1
        seen_coordinates.add(coordinate_key)

        if normalized_name and normalized_name in seen_names:
            duplicate_name_count += 1
        if normalized_name:
            seen_names.add(normalized_name)

        description = placemark.findtext(
            "kml:description", default="", namespaces=NS
        ).strip()

        features.append({
            "type": "Feature",
            "id": f"hyd-flood-location-{index:03d}",
            "geometry": {
                "type": "Point",
                "coordinates": [longitude, latitude],
            },
            "properties": {
                "location_id": f"hyd-flood-location-{index:03d}",
                "name": name or f"Unnamed location {index}",
                "source_id": "opencity-hyderabad-flooding-locations",
                "source_description": description or None,
                "record_type": "mapped_flooding_location",
                "data_origin": "real",
                "occurrence_time_known": False,
                "severity_known": False,
                "verification_status": "not_independently_verified",
            },
        })

    if not features:
        raise ValueError("No point features found in the KML file.")

    return {
        "type": "FeatureCollection",
        "features": features,
        "_audit": {
            "feature_count": len(features),
            "duplicate_coordinate_count": duplicate_coordinate_count,
            "duplicate_name_count": duplicate_name_count,
        },
    }


def main():
    result = convert_kml(SOURCE_FILE)
    audit = result.pop("_audit")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    coordinates = [
        feature["geometry"]["coordinates"]
        for feature in result["features"]
    ]
    longitudes = [point[0] for point in coordinates]
    latitudes = [point[1] for point in coordinates]

    manifest = {
        "dataset_name": "Hyderabad Mapped Flooding Locations",
        "source_provider": "OpenCity",
        "source_page": SOURCE_PAGE,
        "original_file": str(SOURCE_FILE),
        "output_file": str(OUTPUT_FILE),
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "format": "GeoJSON",
        "coordinate_reference_system": "OGC:CRS84 longitude, latitude order",
        "feature_count": audit["feature_count"],
        "duplicate_coordinate_count": audit["duplicate_coordinate_count"],
        "duplicate_name_count": audit["duplicate_name_count"],
        "bounds_west_south_east_north": [
            min(longitudes),
            min(latitudes),
            max(longitudes),
            max(latitudes),
        ],
        "license": (
            "Check the source page and resource metadata; retain attribution."
        ),
        "limitations": [
            "Mapped flooding locations are not timestamped incident events.",
            "No occurrence times or severity labels were present in the inspected KML.",
            "Locations have not been independently verified by this pipeline.",
            "Do not use these points alone as supervised ML target labels.",
        ],
    }

    MANIFEST_FILE.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"GeoJSON saved: {OUTPUT_FILE}")
    print(f"Manifest saved: {MANIFEST_FILE}")
    print(f"Features: {audit['feature_count']}")
    print(f"Duplicate coordinates: {audit['duplicate_coordinate_count']}")
    print(f"Duplicate names: {audit['duplicate_name_count']}")
    print(f"Bounds (west, south, east, north): {manifest['bounds_west_south_east_north']}")


if __name__ == "__main__":
    main()
