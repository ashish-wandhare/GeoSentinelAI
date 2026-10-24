
import html
import json
from pathlib import Path

import folium
import streamlit as st
from streamlit_folium import st_folium

DATA_FILE = Path("data/processed/hyderabad_flooding_points.geojson")
HOTSPOT_FILE = Path("data/processed/hyderabad_flooding_hotspots.geojson")

st.set_page_config(
    page_title="GeoSentinel AI | Flooding Hotspots",
    page_icon="🌧️",
    layout="wide",
)

st.title("GeoSentinel AI")
st.subheader("Hyderabad Flooding Hotspots")
st.caption(
    "Explore mapped flooding locations and their geographic concentration. "
    "These data do not represent live incidents or flood predictions."
)

if not DATA_FILE.exists():
    st.error(f"Flooding-location dataset not found: {DATA_FILE}")
    st.stop()

with DATA_FILE.open("r", encoding="utf-8") as file:
    geojson = json.load(file)

features = geojson.get("features", [])
features = [
    feature
    for feature in features
    if feature.get("geometry", {}).get("type") == "Point"
    and len(feature["geometry"].get("coordinates", [])) >= 2
]

if not features:
    st.warning("No valid flooding-location points are available.")
    st.stop()

latitudes = [
    feature["geometry"]["coordinates"][1] for feature in features
]
longitudes = [
    feature["geometry"]["coordinates"][0] for feature in features
]
center = [
    sum(latitudes) / len(latitudes),
    sum(longitudes) / len(longitudes),
]

show_grid = st.checkbox("Show concentration grid", value=True)

hotspot_features = []
if show_grid:
    if HOTSPOT_FILE.exists():
        with HOTSPOT_FILE.open("r", encoding="utf-8") as file:
            hotspot_geojson = json.load(file)
        hotspot_features = hotspot_geojson.get("features", [])
    else:
        st.warning(
            "Hotspot grid not found. Run the hotspot analysis module first."
        )

col1, col2, col3 = st.columns(3)
col1.metric("Mapped locations", len(features))
col2.metric(
    "Occupied grid cells",
    len(hotspot_features) if show_grid else "Hidden",
)
col3.metric("Live waterlogging status", "Unknown")

flood_map = folium.Map(
    location=center,
    zoom_start=13,
    tiles="OpenStreetMap",
)

# Draw concentration cells first so location markers remain visible.
for feature in hotspot_features:
    geometry = feature.get("geometry", {})
    if geometry.get("type") != "Polygon":
        continue

    properties = feature.get("properties", {})
    count = properties.get("mapped_location_count", 0)

    if count >= 5:
        fill_color = "#d73027"
    elif count >= 2:
        fill_color = "#fc8d59"
    else:
        fill_color = "#fee08b"

    folium.GeoJson(
        feature,
        style_function=lambda _feature, color=fill_color: {
            "fillColor": color,
            "color": color,
            "weight": 1,
            "fillOpacity": 0.35,
        },
        tooltip=f"Mapped locations in cell: {count}",
        popup=folium.Popup(
            f"Mapped locations in cell: {count}<br>"
            "This is location concentration, not flood risk.",
            max_width=300,
        ),
    ).add_to(flood_map)

for feature in features:
    longitude, latitude = feature["geometry"]["coordinates"]
    properties = feature.get("properties", {})
    name = html.escape(str(properties.get("name") or "Unnamed location"))

    popup_html = (
        f"<b>{name}</b><br>"
        f"Latitude: {latitude:.6f}<br>"
        f"Longitude: {longitude:.6f}<br>"
        "Type: Mapped flooding location<br>"
        "Live status: Unknown"
    )

    folium.Marker(
        location=[latitude, longitude],
        tooltip=name,
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(flood_map)

st_folium(
    flood_map,
    use_container_width=True,
    height=650,
    returned_objects=[],
)

st.info(
    "Red markers identify locations in the source inventory. "
    "Grid cells show the number of mapped locations per cell. "
    "Neither indicates active flooding or predicts future waterlogging."
)
