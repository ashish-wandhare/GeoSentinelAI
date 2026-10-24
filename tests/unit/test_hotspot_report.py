
import pytest

from src.geospatial.hotspot_report import build_report


def make_points():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [78.40, 17.35],
                },
                "properties": {"name": "Location A"},
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [78.41, 17.36],
                },
                "properties": {"name": "Location B"},
            },
        ],
    }


def make_hotspots():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [78.40, 17.35],
                        [78.42, 17.35],
                        [78.42, 17.37],
                        [78.40, 17.37],
                        [78.40, 17.35],
                    ]],
                },
                "properties": {"mapped_location_count": 2},
            }
        ],
    }


def test_report_counts_and_bounds():
    report = build_report(make_points(), make_hotspots())

    assert report["summary"]["mapped_point_count"] == 2
    assert report["summary"]["occupied_grid_cell_count"] == 1
    assert report["summary"]["total_locations_counted_in_grid"] == 2
    assert report["summary"]["maximum_locations_per_cell"] == 2

    assert report["geographic_bounds_wgs84"] == {
        "west": 78.40,
        "south": 17.35,
        "east": 78.41,
        "north": 17.36,
    }


def test_report_identifies_analysis_as_not_a_prediction():
    report = build_report(make_points(), make_hotspots())

    assert report["analysis_type"] == "mapped_location_concentration"
    assert report["data_provenance"]["independently_verified"] is False
    assert report["data_provenance"]["occurrence_timestamps_available"] is False
    assert any(
        "not flood probability" in limitation
        for limitation in report["limitations"]
    )


def test_report_rejects_inconsistent_point_and_grid_counts():
    hotspots = make_hotspots()
    hotspots["features"][0]["properties"]["mapped_location_count"] = 1

    with pytest.raises(ValueError, match="does not match"):
        build_report(make_points(), hotspots)


def test_report_handles_empty_datasets():
    empty = {"type": "FeatureCollection", "features": []}

    report = build_report(empty, empty)

    assert report["summary"]["mapped_point_count"] == 0
    assert report["summary"]["occupied_grid_cell_count"] == 0
    assert report["summary"]["maximum_locations_per_cell"] == 0
    assert report["geographic_bounds_wgs84"] is None
