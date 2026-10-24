import geopandas as gpd
from shapely.geometry import box

BOUNDARY_FILE = "data/raw/india_adm2_boundaries.geojson"

def main():
    gdf = gpd.read_file(BOUNDARY_FILE).to_crs("EPSG:4326")

    # Approximate Hyderabad-region search window.
    # This is a search area, NOT an official city boundary.
    search_area = box(77.7, 16.7, 79.3, 17.9)

    nearby = gdf[gdf.geometry.intersects(search_area)].copy()

    if nearby.empty:
        print("No administrative polygons intersect the search area.")
        return

    nearby["west"] = nearby.geometry.bounds["minx"]
    nearby["south"] = nearby.geometry.bounds["miny"]
    nearby["east"] = nearby.geometry.bounds["maxx"]
    nearby["north"] = nearby.geometry.bounds["maxy"]

    print(f"Polygons intersecting search area: {len(nearby)}")
    print("\nNearby administrative areas:")
    print(
        nearby[
            ["shapeName", "shapeISO", "west", "south", "east", "north"]
        ].to_string(index=False)
    )

if __name__ == "__main__":
    main()