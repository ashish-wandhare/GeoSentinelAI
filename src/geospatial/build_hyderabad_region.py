
import json
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box

SOURCE_FILE = Path("data/raw/india_adm2_boundaries.geojson")
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "hyderabad_region_districts.geojson"
MANIFEST_FILE = OUTPUT_DIR / "hyderabad_region_manifest.json"

# Approximate search window only; not an official city boundary.
SEARCH_AREA = box(77.7, 16.7, 79.3, 17.9)


def main():
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"Boundary source file not found: {SOURCE_FILE}"
        )

    districts = gpd.read_file(SOURCE_FILE).to_crs("EPSG:4326")

    nearby = districts[
        districts.geometry.intersects(SEARCH_AREA)
    ].copy()

    if nearby.empty:
        raise ValueError("No districts intersect the search area.")

    if nearby.geometry.isna().any():
        raise ValueError("Missing geometries found.")

    if not nearby.geometry.is_valid.all():
        raise ValueError("Invalid geometries found.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    nearby.to_file(OUTPUT_FILE, driver="GeoJSON")

    manifest = {
        "dataset_name": "Hyderabad Region District Boundaries",
        "provider": "geoBoundaries",
        "source_file": str(SOURCE_FILE),
        "output_file": str(OUTPUT_FILE),
        "source_boundary_type": "ADM2",
        "country_iso3": "IND",
        "license": "CC BY 4.0; verify source metadata and retain attribution",
        "coordinate_reference_system": "EPSG:4326",
        "feature_count": len(nearby),
        "selection_method": (
            "District polygons intersecting an approximate Hyderabad-region "
            "bounding box; this is not an official GHMC boundary."
        ),
        "search_bounds_west_south_east_north": [
            77.7, 16.7, 79.3, 17.9
        ],
        "limitations": [
            "District boundaries are not municipal boundaries.",
            "This dataset does not contain waterlogging incident labels.",
            "Spatial intersection does not mean a whole district lies inside "
            "the search window."
        ]
    }

    MANIFEST_FILE.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    print(f"Saved regional boundaries: {OUTPUT_FILE}")
    print(f"Saved manifest: {MANIFEST_FILE}")
    print(f"Features: {len(nearby)}")
    print(f"CRS: {nearby.crs}")
    print(f"Invalid geometries: {(~nearby.geometry.is_valid).sum()}")
    print("\nIncluded districts:")
    print(nearby["shapeName"].sort_values().to_string(index=False))


if __name__ == "__main__":
    main()
