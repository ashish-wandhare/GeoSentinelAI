
from pathlib import Path
import xml.etree.ElementTree as ET

KML_FILE = Path("data/raw/hyderabad_flooding_points.kml")

NS = {
    "kml": "http://www.opengis.net/kml/2.2",
}


def main():
    if not KML_FILE.exists():
        raise FileNotFoundError(
            f"KML file not found: {KML_FILE}\n"
            "Download the Hyderabad flooding points KML first."
        )

    root = ET.parse(KML_FILE).getroot()
    placemarks = root.findall(".//kml:Placemark", NS)

    print(f"File: {KML_FILE}")
    print(f"Placemark features: {len(placemarks)}")

    geometry_counts = {
        "Point": 0,
        "LineString": 0,
        "Polygon": 0,
        "Other": 0,
    }

    for placemark in placemarks:
        name = placemark.findtext("kml:name", default="", namespaces=NS)
        description = placemark.findtext(
            "kml:description", default="", namespaces=NS
        )

        geometry = None
        for kind in ("Point", "LineString", "Polygon"):
            if placemark.find(f".//kml:{kind}", NS) is not None:
                geometry = kind
                break

        if geometry is None:
            geometry = "Other"

        geometry_counts[geometry] += 1

        coordinates = []
        for element in placemark.findall(".//kml:coordinates", NS):
            if element.text:
                coordinates.extend(element.text.split())

        print(f"\nName: {name or '(unnamed)'}")
        print(f"Geometry: {geometry}")
        print(f"Description: {description[:250] or '(none)'}")
        print(f"Coordinate samples: {coordinates[:3]}")

    print("\nGeometry summary:")
    for geometry, count in geometry_counts.items():
        print(f"{geometry}: {count}")


if __name__ == "__main__":
    main()
