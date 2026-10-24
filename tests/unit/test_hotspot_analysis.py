
import json

from src.geospatial.hotspot_analysis import build_hotspots


def test_every_point_is_counted_once():
    points = [
        {"longitude": 78.40, "latitude": 17.35, "name": "A"},
        {"longitude": 78.41, "latitude": 17.36, "name": "B"},
        {"longitude": 78.50, "latitude": 17.45, "name": "C"},
    ]

    result = build_hotspots(points)

    total = sum(
        feature["properties"]["mapped_location_count"]
        for feature in result["features"]
    )

    assert total == len(points)


def test_points_in_same_cell_are_grouped(monkeypatch):
    import src.geospatial.hotspot_analysis as module

    monkeypatch.setattr(module, "GRID_SIZE", 0.05)

    points = [
        {"longitude": 78.401, "latitude": 17.351, "name": "A"},
        {"longitude": 78.402, "latitude": 17.352, "name": "B"},
    ]

    result = module.build_hotspots(points)

    assert len(result["features"]) == 1
    assert result["features"][0]["properties"]["mapped_location_count"] == 2


def test_output_contains_valid_geojson_polygon_structure():
    points = [
        {"longitude": 78.40, "latitude": 17.35, "name": "A"},
    ]

    result = build_hotspots(points)

    assert result["type"] == "FeatureCollection"
    feature = result["features"][0]
    assert feature["geometry"]["type"] == "Polygon"
    assert len(feature["geometry"]["coordinates"][0]) == 5
    assert feature["properties"]["is_flooding_prediction"] is False


def test_empty_points_produce_empty_feature_collection():
    result = build_hotspots([])

    assert result == {"type": "FeatureCollection", "features": []}
