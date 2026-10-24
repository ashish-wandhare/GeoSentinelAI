import json
from pathlib import Path

import geopandas as gpd
import httpx


METADATA_URL = (
    "https://www.geoboundaries.org/api/current/"
    "gbOpen/IND/ADM2/"
)

OUTPUT_DIR = Path("data/raw")
GEOJSON_PATH = OUTPUT_DIR / "india_adm2_boundaries.geojson"
METADATA_PATH = OUTPUT_DIR / "india_adm2_manifest.json"


def download_boundary_metadata() -> dict:
    """Retrieve metadata for India's open ADM2 boundaries."""

    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        response = client.get(METADATA_URL)
        response.raise_for_status()
        metadata = response.json()

    if not isinstance(metadata, dict):
        raise ValueError(
            "Expected one boundary metadata object; "
            "inspect the API response before continuing."
        )

    download_url = metadata.get("simplifiedGeometryGeoJSON")

    if not download_url:
        download_url = metadata.get("gjDownloadURL")

    if not download_url:
        raise ValueError("No GeoJSON download URL in API metadata.")

    if not download_url.startswith("https://"):
        raise ValueError("Expected a secure HTTPS download URL.")

    return metadata


def download_geojson(url: str) -> None:
    """Download the boundary GeoJSON."""

    with httpx.Client(timeout=120.0, follow_redirects=True) as client:
        with client.stream("GET", url) as response:
            response.raise_for_status()

            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            with GEOJSON_PATH.open("wb") as file:
                for chunk in response.iter_bytes():
                    file.write(chunk)


def inspect_boundaries() -> None:
    """Inspect CRS, geometry quality and Hyderabad name candidates."""

    gdf = gpd.read_file(GEOJSON_PATH)

    if gdf.empty:
        raise ValueError("Downloaded boundary layer is empty.")

    if gdf.crs is None:
        raise ValueError("Boundary layer has no declared CRS.")

    print(f"Features: {len(gdf)}")
    print(f"CRS: {gdf.crs}")
    print(f"Columns: {list(gdf.columns)}")
    print(f"Invalid geometries: {(~gdf.geometry.is_valid).sum()}")
    print(f"Missing geometries: {gdf.geometry.isna().sum()}")

    # Geographic coordinates should be longitude/latitude.
    geographic = gdf.to_crs("EPSG:4326")
    print(f"Geographic bounds: {geographic.total_bounds.tolist()}")

    name_columns = [
        column for column in gdf.columns
        if any(word in column.lower() for word in ("name", "shape"))
    ]

    for column in name_columns:
        matches = geographic[
            geographic[column].astype("string")
            .str.contains("hyderabad", case=False, na=False)
        ]

        if not matches.empty:
            print(f"\nHyderabad candidates in {column}:")
            print(matches[[column, "geometry"]].head(10).to_string())

    print("\nAvailable attributes:")
    print(gdf.drop(columns="geometry").head(5).to_string(index=False))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Retrieving geoBoundaries metadata...")
    metadata = download_boundary_metadata()

    download_url = metadata.get("simplifiedGeometryGeoJSON")
    if not download_url:
        download_url = metadata["gjDownloadURL"]

    print(f"Boundary ID: {metadata.get('boundaryID')}")
    print(f"Boundary type: {metadata.get('boundaryType')}")
    print(f"Source: {metadata.get('source')}")

    print("Downloading GeoJSON...")
    download_geojson(download_url)

    manifest = {
        "provider": "geoBoundaries",
        "api_url": METADATA_URL,
        "boundary_type_requested": "ADM2",
        "country_iso3": "IND",
        "licence": "CC BY 4.0; verify dataset-specific terms",
        "metadata": metadata,
        "downloaded_file": str(GEOJSON_PATH),
    }

    METADATA_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Saved boundary data: {GEOJSON_PATH}")
    print(f"Saved manifest: {METADATA_PATH}")

    inspect_boundaries()


if __name__ == "__main__":
    main()