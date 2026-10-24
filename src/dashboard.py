

"""GeoSentinel AI — Glassmorphic environmental intelligence dashboard."""



from pathlib import Path



import folium

import pandas as pd

import plotly.graph_objects as go

import requests

import streamlit as st

from streamlit_folium import st_folium

try:
    from streamlit_geolocation import streamlit_geolocation
except ImportError:
    streamlit_geolocation = None





ROOT = Path(__file__).resolve().parents[1]

API = "http://127.0.0.1:8000"



ANOMALY_FILE = (

    ROOT / "artifacts" / "rainfall_anomaly_baseline"

    / "rainfall_anomaly_results.csv"

)



st.set_page_config(

    page_title="GeoSentinel AI | Intelligence Center",

    page_icon="🌧️",

    layout="wide",

    initial_sidebar_state="expanded",

)
# ----------------------------- THEME -----------------------------
st.markdown(

    """

    <style>

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght\@400;500;600;700;800&display=swap');



    :root {

        color-scheme: dark;

        --bg: #061321;

        --panel: rgba(13, 34, 55, .78);

        --panel2: rgba(15, 45, 68, .68);

        --border: rgba(61, 178, 224, .32);

        --teal: #20E0D0;

        --cyan: #35BFFF;

        --muted: #91ABC4;

        --white: #F1F7FF;

    }



    html, body, [class*="css"] {

        font-family: 'Inter', sans-serif;

    }



    .stApp {
        color: var(--white);
        background-color: #04101d;
        background-image:
            linear-gradient(115deg, rgba(3, 13, 26, .92) 0%, rgba(4, 20, 36, .82) 48%, rgba(3, 15, 28, .91) 100%),
            radial-gradient(ellipse at 78% 4%, rgba(0, 190, 220, .18), transparent 38%),
            radial-gradient(ellipse at 4% 70%, rgba(0, 89, 160, .15), transparent 35%),
            url("https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=2400&q=85");
        background-size: cover, cover, cover, cover;
        background-position: center, center, center, center;
        background-attachment: fixed;
    }



    [data-testid="stAppViewContainer"],

    [data-testid="stMain"],

    [data-testid="stMainBlockContainer"] {

        background: transparent !important;

    }

    [data-testid="stVerticalBlockBorderWrapper"] > div,
    [data-testid="stExpander"] details,
    [data-testid="stPopover"] > div {
        background-color: rgba(4, 22, 38, .70) !important;
        border-color: rgba(43, 178, 218, .28) !important;
    }

    [data-testid="stDataFrame"], [data-testid="stTable"] {
        background: rgba(4, 20, 35, .88) !important;
    }

    [data-testid="stMetric"] {
        background: rgba(5, 26, 44, .82) !important;
        border-color: rgba(44, 177, 216, .28) !important;
    }

    .stMarkdown, [data-testid="stMarkdownContainer"] {
        color: #D8EAF7;
    }



    [data-testid="stHeader"] {

        background: rgba(5, 17, 29, .78) !important;

    }



    [data-testid="stToolbar"] {

        background: transparent !important;

    }



    .block-container {

        max-width: 1800px;

        padding-top: 1.15rem;

        padding-bottom: 2rem;

    }



    [data-testid="stSidebar"] {

        background: rgba(2, 13, 25, .94) !important;
        backdrop-filter: blur(18px);

        border-right: 1px solid rgba(53, 191, 255, .25);

    }



    [data-testid="stSidebar"] * {

        color: #D9EAF9;

    }



    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {

        color: var(--muted);

    }



    .brand {

        font-size: 26px;

        font-weight: 800;

        letter-spacing: -1px;

        color: #F5FBFF;

    }



    .brand span {

        color: var(--teal);

    }



    .brand-sub {

        color: #8EADC8;

        font-size: 9px;

        letter-spacing: 2.3px;

        margin-top: 5px;

    }



    .hero {

        position: relative;

        overflow: hidden;

        background:

            linear-gradient(110deg,

                rgba(13, 34, 57, .95),

                rgba(10, 53, 76, .84) 64%,

                rgba(0, 122, 145, .60));

        border: 1px solid rgba(63, 190, 231, .38);

        border-radius: 18px;

        padding: 27px 28px;

        margin-bottom: 17px;

        box-shadow: inset 0 1px 0 rgba(60,220,240,.08),
                    0 14px 42px rgba(0,0,0,.32), 0 0 28px rgba(0,180,220,.06);

    }



    .eyebrow {

        color: var(--teal);

        font-size: 10px;

        font-weight: 800;

        letter-spacing: 2.5px;

        margin-bottom: 10px;

    }



    .hero h1 {

        font-size: clamp(25px, 2.3vw, 38px);

        line-height: 1.2;

        font-weight: 800;

        color: #FFFFFF !important;

        letter-spacing: -1px;

        margin: 0 0 10px 0;

    }



    .hero h1 span {

        color: var(--teal);

    }



    .hero p {

        color: #D0E3F4 !important;

        font-size: 13px;

        margin: 0;

        line-height: 1.7;

    }



    .hero-meta {

        border: 1px solid rgba(102, 196, 225, .25);

        background: rgba(4, 22, 38, .35);

        border-radius: 13px;

        padding: 14px;

        height: 100%;

    }



    .hero-meta-label {

        font-size: 10px;

        color: #89B5D0;

        letter-spacing: 1px;

        text-transform: uppercase;

    }



    .hero-meta-value {

        font-size: 16px;

        color: white;

        font-weight: 700;

        margin-top: 7px;

    }



    .hero-meta-note {

        font-size: 10px;

        color: #9DB8CF;

        margin-top: 5px;

    }



    .section-title {

        color: #F0F7FF;

        font-size: 18px;

        font-weight: 750;

        margin: 17px 0 10px;

    }



    .section-note {

        color: #8FAAC2;

        font-size: 11px;

        margin: -5px 0 12px;

    }



    .glass-card {
        background: linear-gradient(145deg, rgba(7, 30, 49, .88), rgba(3, 17, 31, .82));
        border: 1px solid rgba(38, 190, 224, .38);
        border-radius: 14px;
        padding: 17px 18px;
        min-height: 124px;
        box-shadow: inset 0 1px 0 rgba(75, 220, 244, .07), 0 10px 28px rgba(0,0,0,.28);
        backdrop-filter: blur(16px);
    }



    .glass-card:hover {

        border-color: rgba(32, 224, 208, .72);

        box-shadow: 0 0 24px rgba(32, 224, 208, .08);

    }



    .kpi-label {

        color: #A7C1D8;

        font-size: 10px;

        font-weight: 700;

        letter-spacing: .8px;

        margin-bottom: 11px;

    }



    .kpi-value {

        color: #F7FBFF;

        font-size: 28px;

        font-weight: 800;

        line-height: 1.2;

    }



    .kpi-note {

        color: #8EABC4;

        font-size: 10px;

        margin-top: 9px;

    }



    .kpi-accent {

        color: var(--teal);

    }



    .glass-panel {

        background: linear-gradient(145deg, rgba(5, 28, 47, .88), rgba(3, 17, 31, .86));

        border: 1px solid var(--border);

        border-radius: 15px;

        padding: 16px;

        box-shadow: inset 0 1px 0 rgba(255,255,255,.035),

                    0 8px 25px rgba(0,0,0,.12);

        backdrop-filter: blur(12px);

    }



    .panel-title {

        font-size: 14px;

        font-weight: 750;

        color: #F0F7FF;

        margin-bottom: 3px;

    }



    .panel-subtitle {

        color: #8EAAC4;

        font-size: 10px;

        margin-bottom: 10px;

    }



    .status-pill {

        display: inline-block;

        background: rgba(18, 190, 152, .13);

        border: 1px solid rgba(32, 224, 190, .40);

        color: #6CF0D1;

        border-radius: 30px;

        padding: 7px 12px;

        font-size: 10px;

        font-weight: 800;

        letter-spacing: .6px;

    }



    .status-dot {

        color: #31E4A7;

    }



    .stApp p, .stApp label, .stApp li {

        color: #D5E5F4;

    }



    [data-testid="stMetric"] {

        background: rgba(14, 39, 61, .80);

        border: 1px solid rgba(61, 178, 224, .28);

        border-radius: 12px;

        padding: 12px 14px;

    }



    [data-testid="stMetricLabel"] {

        color: #9DB7CF !important;

    }



    [data-testid="stMetricValue"] {

        color: #F5FBFF !important;

    }



    [data-testid="stDataFrame"] {

        border: 1px solid var(--border);

        border-radius: 12px;

        overflow: hidden;

    }



    [data-baseweb="select"] > div,

    [data-baseweb="input"] > div,

    [data-baseweb="textarea"] {

        background: rgba(13, 35, 55, .95) !important;

        border-color: #31536D !important;

        color: #F1F7FF !important;

    }



    .stButton > button {

        background: linear-gradient(120deg, #0D6177, #087F8C);

        color: white;

        border: 1px solid rgba(57, 221, 218, .55);

        border-radius: 9px;

        font-weight: 700;

        min-height: 38px;

        box-shadow: 0 0 15px rgba(32, 224, 208, .08);

    }



    .stButton > button:hover {

        background: linear-gradient(120deg, #0D8291, #0A9B9D);

        color: white;

        border-color: #45F1DF;

        box-shadow: 0 0 19px rgba(32, 224, 208, .19);

    }



    [data-testid="stRadio"] label {

        color: #D9EAF9 !important;

    }



    [data-testid="stAlert"] {

        background: rgba(13, 38, 59, .85);

        border-radius: 10px;

    }



    [data-testid="stCaptionContainer"] {

        color: #8EAAC4;

    }



    hr {

        border-color: rgba(65, 139, 179, .28);

    }



    footer {

        visibility: hidden;

    }





/* Glassmorphic dark dataframe */

[data-testid="stDataFrame"] {

    background: rgba(10, 28, 45, 0.88) !important;

    border: 1px solid rgba(32, 224, 208, 0.32) !important;

    border-radius: 14px !important;

    overflow: hidden !important;

    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.22) !important;

}



/* Streamlit's dataframe canvas */

[data-testid="stDataFrame"] iframe {

    background: transparent !important;

}



/* Dark theme for the dataframe's underlying table */

[data-testid="stDataFrame"] [class*="glideDataEditor"],

[data-testid="stDataFrame"] [class*="gdg"],

[data-testid="stDataFrame"] canvas {

    background-color: #0C2033 !important;

}



/* Keep table headings and cells readable */

[data-testid="stDataFrame"] [role="columnheader"],

[data-testid="stDataFrame"] [role="gridcell"] {

    background-color: #102A40 !important;

    color: #DCECF8 !important;

    border-color: rgba(79, 135, 169, 0.24) !important;

}



/* Dark table wrapper */

[data-testid="stTable"] {

    background: rgba(10, 28, 45, 0.88) !important;

    border: 1px solid rgba(32, 224, 208, 0.28) !important;

    border-radius: 14px !important;

    overflow: hidden !important;

}





    </style>

    """,

    unsafe_allow_html=True,

)
# ----------------------------- DATA -----------------------------
@st.cache_data(ttl=30)

def get_api_data():

    health = requests.get(f"{API}/health", timeout=5)

    health.raise_for_status()



    rainfall = requests.get(

        f"{API}/api/v1/rainfall/latest", timeout=10

    )

    rainfall.raise_for_status()



    hotspots = requests.get(

        f"{API}/api/v1/geospatial/hotspots", timeout=10

    )

    hotspots.raise_for_status()



    return health.json(), rainfall.json(), hotspots.json()





@st.cache_data(ttl=60)

def get_live_weather():

    """Fetch current weather from the live-weather API."""

    response = requests.get(

        f"{API}/api/v1/weather/live",

        timeout=10,

    )

    response.raise_for_status()

    return response.json()



@st.cache_data(ttl=60)
def get_location_weather(latitude, longitude):
    """Fetch weather for user-shared coordinates through the GeoSentinel API."""
    response = requests.get(
        f"{API}/api/v1/weather/location",
        params={"latitude": latitude, "longitude": longitude},
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=60)
def get_location_rainfall_inference(latitude, longitude):
    """Fetch ML rainfall inference for user-shared GPS coordinates."""
    response = requests.get(
        f"{API}/api/v1/rainfall/location-inference",
        params={"latitude": latitude, "longitude": longitude},
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=60)
def get_live_rainfall_inference():

    """Fetch live rainfall ML inference from the API."""

    response = requests.get(

        f"{API}/api/v1/rainfall/live-inference",

        timeout=15,

    )

    response.raise_for_status()

    return response.json()


@st.cache_data(ttl=30)
def get_warning_history(limit=100):
    """Read explicitly recorded rainfall evaluations from the API."""
    response = requests.get(
        f"{API}/api/v1/warnings/history",
        params={"limit": limit},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def record_warning_evaluation(inference_result):
    """Explicitly save one location-specific inference result."""
    response = requests.post(
        f"{API}/api/v1/warnings/record",
        json=inference_result,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=15)
def get_alert_history(limit=100):
    """Fetch persisted alert-management records from the API."""
    response = requests.get(
        f"{API}/api/v1/alerts/history",
        params={"limit": limit},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def evaluate_alerts(payload):
    """Submit one rainfall evaluation to the prototype alert rules."""
    response = requests.post(
        f"{API}/api/v1/alerts/evaluate",
        json=payload,
        timeout=15,
    )
    response.raise_for_status()
    return response.json()


def update_alert_status(alert_id, status):
    """Update an alert lifecycle status through the API."""
    response = requests.patch(
        f"{API}/api/v1/alerts/{int(alert_id)}/status",
        json={"status": status},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=30)

def get_history():

    if not ANOMALY_FILE.exists():

        return pd.DataFrame()



    df = pd.read_csv(ANOMALY_FILE)

    if df.empty or "observed_at" not in df.columns:

        return pd.DataFrame()



    df["observed_at"] = pd.to_datetime(

        df["observed_at"], utc=True, errors="coerce"

    )

    df = df.dropna(subset=["observed_at"]).sort_values("observed_at")



    for col in [

        "precipitation_mm",

        "rainfall_rolling_3h_mm",

        "rainfall_rolling_6h_mm",

        "rainfall_rolling_24h_mm",

        "anomaly_score",

    ]:

        if col in df:

            df[col] = pd.to_numeric(df[col], errors="coerce")



    if "anomaly_flag" in df:

        df["anomaly_flag"] = (

            df["anomaly_flag"].astype(str).str.lower().isin(["true", "1"])

        )



    return df





try:

    health, rainfall, hotspot_response = get_api_data()

    api_online = True

    api_error = ""

except (requests.RequestException, ValueError, KeyError) as exc:

    health, rainfall, hotspot_response = {}, {}, {}

    api_online = False

    api_error = str(exc)



history = get_history()

geojson = hotspot_response.get("geojson", {})

hotspot_features = geojson.get("features", [])



observation_count = len(history)

anomaly_count = (

    int(history["anomaly_flag"].sum())

    if observation_count and "anomaly_flag" in history

    else 0

)

anomaly_rate = (

    anomaly_count / observation_count * 100 if observation_count else 0

)

mapped_locations = sum(

    int((f.get("properties") or {}).get("mapped_location_count", 0))

    for f in hotspot_features

)

start_label = (

    history["observed_at"].min().strftime("%d %b %Y")

    if observation_count else "Unavailable"

)

end_label = (

    history["observed_at"].max().strftime("%d %b %Y")

    if observation_count else "Unavailable"

)
# ----------------------------- SIDEBAR -----------------------------
with st.sidebar:
    # Keep the HTML on one line so Markdown does not interpret indentation as a code block.
    st.markdown(
        '<div style="padding:10px 0 24px">'
        '<div class="brand">🌧️ <span>GEO</span>SENTINEL AI</div>'
        '<div class="brand-sub">ENVIRONMENTAL INTELLIGENCE</div>'
        '</div>',
        unsafe_allow_html=True,
    )



    page = st.radio(

        "NAVIGATION",

        [

            "Executive Overview",

            "Warning History",

            "Alert Management",

            "Rainfall Analytics",

            "Geospatial Intelligence",

            "Data & Model Status",

        ],

        label_visibility="visible",

    )



    st.divider()

    st.markdown("PROJECT INFO")

    st.markdown("GeoSentinel AI")

    st.caption("Urban Waterlogging Intelligence")

    st.markdown("Location")

    st.caption("Hyderabad · Prototype")

    st.markdown("Build Version")

    st.caption("0.2.0 · Glass UI")

    st.markdown("Data Mode")

    st.caption("Historical · Jun–Aug 2025")



    st.markdown("Model")

    st.caption("Isolation Forest")



    if api_online:

        st.markdown(

            '<span class="status-pill"><span class="status-dot">●</span> '

            'API CONNECTED</span>',

            unsafe_allow_html=True,

        )

    else:

        st.error("API disconnected")



    st.markdown(

        """

        <div style="

            margin-top:28px;

            padding:15px;

            border:1px solid rgba(61,178,224,.25);

            border-radius:12px;

            background:linear-gradient(145deg,rgba(15,48,72,.8),rgba(5,22,38,.8));

        ">

          <div style="color:#20E0D0;font-size:10px;letter-spacing:1.5px">

            GEOSPATIAL INTELLIGENCE

          </div>

          <div style="color:#EAF6FF;font-size:17px;font-weight:800;margin-top:7px">

            Hyderabad

          </div>

          <div style="color:#91ABC4;font-size:11px;margin-top:5px">

            Building resilient cities with GeoAI

          </div>

        </div>

        """,

        unsafe_allow_html=True,

    )
# ----------------------------- HEADER -----------------------------
top_left, top_right = st.columns([2.4, 1])



with top_left:

    st.markdown(

        """

        <div class="hero">

          <div class="eyebrow">GEOAI · RAINFALL INTELLIGENCE · HYDERABAD</div>

          <h1>Environmental <span>Intelligence Center</span></h1>

          <p>GeoAI-Powered Urban Waterlogging Intelligence & Early Warning Platform</p>

          <div style="margin-top:18px;color:#8DCFE5;font-size:11px">

            ◈ Rainfall Analytics    ◈ Anomaly Detection   

            ◈ Geospatial Intelligence    ◈ Risk Monitoring

          </div>

        </div>

        """,

        unsafe_allow_html=True,

    )



with top_right:

    st.markdown('<div class="hero-meta">', unsafe_allow_html=True)

    st.markdown('<div class="hero-meta-label">LOCATION MONITORING</div>',

                unsafe_allow_html=True)

    st.markdown('<div class="hero-meta-value">⌖ Hyderabad, India</div>',

                unsafe_allow_html=True)

    st.markdown(

        '<div class="hero-meta-note">Historical data mode · Not live conditions</div>',

        unsafe_allow_html=True,

    )

    st.write("")

    if st.button("↻ Refresh intelligence", use_container_width=True):

        get_api_data.clear()

        get_history.clear()

        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)



if not api_online:

    st.error(f"API unavailable: {api_error}")

    st.info("Start the API with `python -m uvicorn src.api:app --reload`.")

    st.stop()



st.markdown(

    f'<span class="status-pill">● API CONNECTED</span> '

    f'<span style="color:#8EAAC4;font-size:11px">'

    f' Latest observation: {rainfall.get("observed_at_utc", "Unavailable")} UTC'

    f' · Mode: HISTORICAL</span>',

    unsafe_allow_html=True,

)
# ----------------------------- KPI CARDS -----------------------------
def kpi(label, value, note, accent=""):

    st.markdown(

        f"""

        <div class="glass-card">

          <div class="kpi-label">{label}</div>

          <div class="kpi-value {accent}">{value}</div>

          <div class="kpi-note">{note}</div>

        </div>

        """,

        unsafe_allow_html=True,

    )





st.markdown('<div class="section-title">Platform overview</div>',

            unsafe_allow_html=True)



c1, c2, c3, c4 = st.columns(4)



with c1:

    kpi("RAINFALL OBSERVATIONS", f"{observation_count:,}",

        "Historical model dataset")



with c2:

    kpi("UNUSUAL PATTERNS", f"{anomaly_count:,}",

        "Isolation Forest detections")



with c3:

    kpi("ANOMALY RATE", f"{anomaly_rate:.2f}%",

        "Share of analyzed observations", "kpi-accent")



with c4:

    kpi("MAPPED LOCATIONS", f"{mapped_locations:,}",

        "Historical mapped inventory", "kpi-accent")
# ----------------------------- CHART HELPERS -----------------------------
def make_chart_layout(fig, height=300):

    fig.update_layout(

        height=height,

        paper_bgcolor="rgba(0,0,0,0)",

        plot_bgcolor="rgba(0,0,0,0)",

        font=dict(family="Inter, sans-serif", color="#BDD1E4", size=10),

        margin=dict(l=12, r=12, t=18, b=12),

        legend=dict(

            orientation="h",

            yanchor="bottom",

            y=1.02,

            xanchor="left",

            x=0,

            bgcolor="rgba(0,0,0,0)",

        ),

        xaxis=dict(

            gridcolor="rgba(91,145,179,.14)",

            linecolor="rgba(91,145,179,.2)",

            zerolinecolor="rgba(91,145,179,.15)",

        ),

        yaxis=dict(

            gridcolor="rgba(91,145,179,.14)",

            linecolor="rgba(91,145,179,.2)",

            zerolinecolor="rgba(91,145,179,.15)",

        ),

    )

    return fig
# ----------------------------- OVERVIEW -----------------------------
if page == "Executive Overview":

    left, right = st.columns([1.55, 1])

    st.subheader("Live ML Risk Monitoring")



# Live Weather Monitoring
    st.markdown(

        '<div class="section-title">Live Weather Monitoring</div>',

        unsafe_allow_html=True,

    )



    try:

        live_weather = get_live_weather()

        current = live_weather["current"]



        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)

        st.markdown(

            '<div class="panel-subtitle">'

            'Open-Meteo · Hyderabad reference point · UTC'

            '</div>',

            unsafe_allow_html=True,

        )



        col1, col2, col3 = st.columns(3)

        col1.metric(

            "Temperature",

            f"{current['temperature_2m']:.1f} °C",

        )

        col2.metric(

            "Current precipitation",

            f"{current['precipitation']:.1f} mm",

        )

        col3.metric(

            "Rain",

            f"{current['rain']:.1f} mm",

        )



        st.caption(

            f"Observation time: {current['time']} UTC · "

            "Weather observations do not confirm waterlogging."

        )

        st.markdown("</div>", unsafe_allow_html=True)



    except (requests.RequestException, KeyError, TypeError, ValueError):

        st.warning(

            "Live weather is temporarily unavailable. "

            "Historical rainfall analytics remain available."

        )


    # User-consented browser GPS weather lookup.
    st.markdown(
        '<div class="section-title">Location-Aware Weather</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="glass-panel">',
        unsafe_allow_html=True,
    )
    st.caption(
        "Share your location only if you choose to. Your browser will ask "
        "for permission before providing coordinates."
    )

    if streamlit_geolocation is None:
        st.info(
            "GPS support needs one additional package. In your project "
            "virtual environment, run: "
            "`python -m pip install streamlit-geolocation`"
        )
    else:
        try:
            gps_location = streamlit_geolocation()
            if (
                isinstance(gps_location, dict)
                and gps_location.get("latitude") is not None
                and gps_location.get("longitude") is not None
            ):
                gps_lat = float(gps_location["latitude"])
                gps_lon = float(gps_location["longitude"])
                st.success(
                    f"Location received: {gps_lat:.5f}, {gps_lon:.5f}"
                )
                location_weather = get_location_weather(gps_lat, gps_lon)
                location_current = location_weather["current"]
                loc_col1, loc_col2, loc_col3 = st.columns(3)
                loc_col1.metric(
                    "Temperature",
                    f"{float(location_current['temperature_2m']):.1f} °C",
                )
                loc_col2.metric(
                    "Precipitation",
                    f"{float(location_current['precipitation']):.1f} mm",
                )
                loc_col3.metric(
                    "Rain",
                    f"{float(location_current['rain']):.1f} mm",
                )
                st.caption(
                    f"Weather observation: {location_current.get('time', 'Unavailable')} UTC"
                )
                st.caption(
                    "Weather is for the coordinates shared by your browser. "
                    "It does not confirm waterlogging or predict flooding."
                )

                st.markdown("#### Location-Specific ML Rainfall Analysis")
                try:
                    location_ml = get_location_rainfall_inference(gps_lat, gps_lon)
                    inference_location = location_ml.get("location", {})
                    st.caption(
                        "Inference coordinates: "
                        f"{float(inference_location.get('latitude', gps_lat)):.5f}, "
                        f"{float(inference_location.get('longitude', gps_lon)):.5f}"
                    )
                    ml_col1, ml_col2, ml_col3 = st.columns(3)
                    ml_col1.metric(
                        "Rolling 3-hour rainfall",
                        f"{float(location_ml['rainfall_rolling_3h_mm']):.1f} mm",
                    )
                    ml_col2.metric(
                        "Rolling 6-hour rainfall",
                        f"{float(location_ml['rainfall_rolling_6h_mm']):.1f} mm",
                    )
                    ml_col3.metric(
                        "Rolling 24-hour rainfall",
                        f"{float(location_ml['rainfall_rolling_24h_mm']):.1f} mm",
                    )

                    risk_level = str(
                        location_ml.get("rainfall_risk_level", "UNAVAILABLE")
                    ).upper()
                    warning_text = location_ml.get(
                        "rainfall_warning",
                        "Location-specific rainfall status is unavailable.",
                    )
                    if risk_level == "VERY HIGH":
                        st.error(f"{risk_level} rainfall level — {warning_text}")
                    elif risk_level == "HIGH":
                        st.warning(f"{risk_level} rainfall level — {warning_text}")
                    elif risk_level == "MODERATE":
                        st.info(f"{risk_level} rainfall level — {warning_text}")
                    elif risk_level == "LOW":
                        st.success(f"{risk_level} rainfall level — {warning_text}")
                    else:
                        st.warning(warning_text)

                    if location_ml.get("unusual_rainfall_pattern", False):
                        st.warning(
                            "The Isolation Forest model flagged an unusual rainfall "
                            "pattern at this location."
                        )
                    else:
                        st.info(
                            "The Isolation Forest model did not flag an unusual "
                            "rainfall pattern at this location."
                        )

                    st.caption(
                        f"Anomaly score: {location_ml.get('anomaly_score', 'Unavailable')} · "
                        f"Observed at: {location_ml.get('observed_at_utc', 'Unavailable')} UTC"
                    )
                    st.caption(
                        "Prototype rainfall thresholds are illustrative and not validated "
                        "flood thresholds. Anomaly scores are not flood probabilities; "
                        "waterlogging is not confirmed."
                    )

                    st.markdown("#### Warning History")
                    st.caption(
                        "Save this evaluation only when you choose. Refreshing the "
                        "dashboard does not automatically create a history record."
                    )
                    if st.button(
                        "Record this evaluation",
                        key="record_location_warning",
                        use_container_width=True,
                    ):
                        try:
                            saved = record_warning_evaluation(location_ml)
                            get_warning_history.clear()
                            st.success(
                                "Evaluation saved to warning history "
                                f"(record ID: {saved.get('id', 'created')})."
                            )
                        except requests.HTTPError as exc:
                            detail = ""
                            try:
                                detail = exc.response.text
                            except (AttributeError, ValueError):
                                pass
                            st.error(
                                "Could not save the evaluation. "
                                f"{exc} {detail}"
                            )
                        except requests.RequestException as exc:
                            st.error(f"Could not reach the API to save the evaluation: {exc}")

                except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
                    st.warning(
                        "Location weather loaded, but location-specific ML inference "
                        f"is temporarily unavailable: {exc}"
                    )
            else:
                st.info(
                    "Select the location component and allow browser location "
                    "permission to load weather for your coordinates."
                )
        except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
            st.warning(f"Location-specific weather is unavailable: {exc}")

    st.markdown("</div>", unsafe_allow_html=True)


    st.subheader("Live ML Risk Monitoring")

    try:
        ml_result = get_live_rainfall_inference()

        col1, col2, col3 = st.columns(3)
        col1.metric("3-Hour Rainfall", f"{ml_result['rainfall_rolling_3h_mm']:.1f} mm")
        col2.metric("6-Hour Rainfall", f"{ml_result['rainfall_rolling_6h_mm']:.1f} mm")
        col3.metric("24-Hour Rainfall", f"{ml_result['rainfall_rolling_24h_mm']:.1f} mm")

        if ml_result["unusual_rainfall_pattern"]:
            st.warning("ML model detected an unusual rainfall pattern.")
        else:
            st.success("ML model detected a typical rainfall pattern.")

        st.caption(
            f"Anomaly score: {ml_result['anomaly_score']:.4f} | "
            f"Observed at: {ml_result['observed_at_utc']}"
        )
        st.caption(
            "This is rainfall anomaly detection, not a waterlogging prediction. "
            "Waterlogging has not been independently verified."
        )
    except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
        st.warning(f"Live ML monitoring is temporarily unavailable: {exc}")


    left, right = st.columns([1.55, 1])



    with left:

        st.markdown('<div class="section-title">Rainfall Monitoring</div>',

                    unsafe_allow_html=True)

        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)

        st.markdown('<div class="panel-title">Hourly Rainfall</div>',

                    unsafe_allow_html=True)

        st.markdown(

            f'<div class="panel-subtitle">{start_label} — {end_label} · mm</div>',

            unsafe_allow_html=True,

        )



        if observation_count and "precipitation_mm" in history:

            fig = go.Figure()

            fig.add_trace(

                go.Scatter(

                    x=history["observed_at"],

                    y=history["precipitation_mm"],

                    name="Hourly rainfall",

                    mode="lines",

                    line=dict(color="#20E0D0", width=1.7),

                    fill="tozeroy",

                    fillcolor="rgba(32,224,208,.12)",

                    hovertemplate="%{x|%d %b %Y %H:%M}<br>%{y:.1f} mm<extra></extra>",

                )

            )

            fig = make_chart_layout(fig, 275)

            fig.update_yaxes(title_text="Rainfall (mm)")

            st.plotly_chart(fig, use_container_width=True,

                            config={"displayModeBar": False})

        else:

            st.info("Rainfall history is unavailable.")



        st.markdown("</div>", unsafe_allow_html=True)



    with right:

        st.markdown('<div class="section-title">Latest Observation</div>',

                    unsafe_allow_html=True)

        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)

        st.markdown(

            f'<div class="panel-title">{rainfall.get("observed_at_utc", "Unavailable")}</div>',

            unsafe_allow_html=True,

        )

        st.markdown(

            '<div class="panel-subtitle">Observation timestamp · UTC</div>',

            unsafe_allow_html=True,

        )



        a, b = st.columns(2)

        a.metric("Hourly rainfall", f"{rainfall['precipitation_mm']:.1f} mm")

        b.metric("Rolling 24h", f"{rainfall['rainfall_rolling_24h_mm']:.1f} mm")



        st.divider()

        st.markdown("Pattern classification")



        if rainfall.get("unusual_rainfall_pattern", False):

            st.warning("Unusual rainfall pattern")

        else:

            st.success("Typical rainfall pattern")



        st.caption(

            f"Anomaly score: {rainfall['anomaly_score']:.4f} · "

            "Not a flood probability."

        )

        st.markdown("</div>", unsafe_allow_html=True)
# Secondary charts
    left, right = st.columns([1.1, 1])



    with left:

        st.markdown('<div class="section-title">Rainfall Accumulation</div>',

                    unsafe_allow_html=True)

        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)



        rolling = [

            col for col in [

                "rainfall_rolling_3h_mm",

                "rainfall_rolling_6h_mm",

                "rainfall_rolling_24h_mm",

            ] if col in history.columns

        ]



        if observation_count and rolling:

            fig = go.Figure()

            colors = ["#35BFFF", "#9B87F5", "#24D6A4"]



            for col, color in zip(rolling, colors):

                label = col.replace("rainfall_rolling_", "").replace("_mm", "")

                fig.add_trace(

                    go.Scatter(

                        x=history["observed_at"],

                        y=history[col],

                        name=label,

                        mode="lines",

                        line=dict(color=color, width=1.5),

                    )

                )



            fig = make_chart_layout(fig, 260)

            fig.update_yaxes(title_text="Rainfall (mm)")

            st.plotly_chart(fig, use_container_width=True,

                            config={"displayModeBar": False})

        else:

            st.info("Rolling rainfall features are unavailable.")



        st.markdown("</div>", unsafe_allow_html=True)



    with right:

        st.markdown('<div class="section-title">Anomaly Distribution</div>',

                    unsafe_allow_html=True)

        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)



        normal_count = max(observation_count - anomaly_count, 0)



        fig = go.Figure(

            data=[

                go.Pie(

                    labels=["Typical pattern", "Unusual pattern"],

                    values=[normal_count, anomaly_count],

                    hole=0.72,

                    marker=dict(

                        colors=["#20D9C2", "#F45B78"],

                        line=dict(color="#0B1E30", width=3),

                    ),

                    textinfo="none",

                    hovertemplate="%{label}<br>%{value:,} (%{percent})<extra></extra>",

                )

            ]

        )

        fig.update_layout(

            height=245,

            paper_bgcolor="rgba(0,0,0,0)",

            plot_bgcolor="rgba(0,0,0,0)",

            font=dict(color="#D6E7F4", family="Inter"),

            margin=dict(l=5, r=5, t=10, b=5),

            showlegend=True,

            legend=dict(

                orientation="h",

                yanchor="bottom",

                y=-0.06,

                xanchor="center",

                x=0.5,

            ),

            annotations=[

                dict(

                    text=f"<b>{observation_count:,}</b><br><span style='font-size:10px'>Total</span>",

                    x=0.5, y=0.5, showarrow=False,

                    font=dict(size=19, color="#F1F7FF"),

                )

            ],

        )

        st.plotly_chart(fig, use_container_width=True,

                        config={"displayModeBar": False})



        st.markdown(

            f'<div class="panel-subtitle" style="text-align:center">'

            f'{normal_count:,} typical · {anomaly_count:,} unusual '

            f'({anomaly_rate:.2f}%)</div>',

            unsafe_allow_html=True,

        )

        st.markdown("</div>", unsafe_allow_html=True)
# Geospatial map
    st.markdown('<div class="section-title">Geospatial Hotspots</div>',

                unsafe_allow_html=True)

    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)

    st.markdown(

        '<div class="panel-subtitle">Historical mapped-location concentration · Not a live flood map</div>',

        unsafe_allow_html=True,

    )



    if hotspot_features:

        coordinates = []



        for feature in hotspot_features:

            geometry = feature.get("geometry") or {}

            if geometry.get("type") == "Polygon":

                for ring in geometry.get("coordinates", []):

                    coordinates.extend(

                        point[:2] for point in ring if len(point) >= 2

                    )



        if coordinates:

            center_lon = sum(p[0] for p in coordinates) / len(coordinates)

            center_lat = sum(p[1] for p in coordinates) / len(coordinates)



            map_obj = folium.Map(

                location=[center_lat, center_lon],

                zoom_start=12,

                tiles="OpenStreetMap",

            )



            folium.GeoJson(

                geojson,

                name="Historical mapped locations",

                style_function=lambda feature: {

                    "color": "#20E0D0",

                    "weight": 1.5,

                    "fillColor": "#087F8C",

                    "fillOpacity": 0.35,

                },

                tooltip=folium.GeoJsonTooltip(

                    fields=["grid_id", "mapped_location_count"],

                    aliases=["Grid cell", "Mapped locations"],

                ),

            ).add_to(map_obj)



            folium.LayerControl().add_to(map_obj)



            st_folium(

                map_obj,

                height=470,

                use_container_width=True,

                key="overview_map",

            )



    st.markdown("</div>", unsafe_allow_html=True)

    # Live rainfall status displayed separately from historical hotspot polygons.
    st.markdown('<div class="section-title">Live Rainfall Status</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    try:
        map_risk = get_live_rainfall_inference()
        risk_level = str(map_risk.get("rainfall_risk_level", "UNAVAILABLE")).upper()
        warning_message = map_risk.get(
            "rainfall_warning", "Live rainfall status is unavailable."
        )
        rolling_3h = map_risk.get("rainfall_rolling_3h_mm")
        observed_at = map_risk.get("observed_at_utc", "Unavailable")

        metric_col, details_col = st.columns([1, 2])
        metric_col.metric("Prototype Rainfall Risk", risk_level)
        details_col.write(warning_message)
        if rolling_3h is not None:
            st.caption(f"Rolling 3-hour rainfall: {float(rolling_3h):.1f} mm")
        st.caption(f"Observation time (UTC): {observed_at}")
        st.caption(
            "Illustrative rainfall thresholds only; not validated flood thresholds. "
            "This status does not confirm waterlogging or predict flooding."
        )
    except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
        st.warning(f"Live rainfall status is temporarily unavailable: {exc}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.caption(
        "Historical hotspot polygons represent mapped historical locations, not live flood zones. "
        "Live rainfall status is displayed separately; GPS tracking and mobile alerts are not connected."
    )
# ----------------------------- WARNING HISTORY PAGE -----------------------------
elif page == "Warning History":
    st.markdown(
        '<div class="section-title">Recorded Rainfall Evaluations</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-note">Only evaluations explicitly saved with the '
        'Record this evaluation button appear here.</div>',
        unsafe_allow_html=True,
    )

    try:
        warning_response = get_warning_history(limit=100)
        warning_records = warning_response.get("records", [])
        record_count = int(warning_response.get("count", len(warning_records)))

        metric_col, status_col = st.columns(2)
        metric_col.metric("Saved evaluations", record_count)
        status_col.metric("Waterlogging confirmed", "No")

        if warning_records:
            warning_df = pd.DataFrame(warning_records)
            preferred_columns = [
                "id",
                "recorded_at_utc",
                "latitude",
                "longitude",
                "risk_level",
                "rainfall_3h_mm",
                "rainfall_6h_mm",
                "rainfall_24h_mm",
                "unusual_rainfall_pattern",
                "anomaly_score",
                "interpretation",
                "waterlogging_confirmed",
                "data_status",
            ]
            visible_columns = [
                col for col in preferred_columns if col in warning_df.columns
            ]
            if "recorded_at_utc" in warning_df.columns:
                warning_df["recorded_at_utc"] = pd.to_datetime(
                    warning_df["recorded_at_utc"], utc=True, errors="coerce"
                ).dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            st.dataframe(
                warning_df[visible_columns],
                use_container_width=True,
                hide_index=True,
            )
            st.download_button(
                "Download warning history as CSV",
                data=warning_df[visible_columns].to_csv(index=False).encode("utf-8"),
                file_name="geosentinel_warning_history.csv",
                mime="text/csv",
            )
        else:
            st.info(
                "No evaluations have been saved yet. Open Executive Overview, "
                "share your location if you choose, and select Record this evaluation."
            )

        st.caption(
            "Risk levels use illustrative, unvalidated rainfall thresholds. "
            "Anomaly scores are not flood probabilities, and saved evaluations "
            "do not confirm waterlogging."
        )
    except (requests.RequestException, ValueError, TypeError) as exc:
        st.error(f"Warning history could not be loaded: {exc}")
        st.info("Check that the GeoSentinel FastAPI service is running.")

# ----------------------------- ALERT MANAGEMENT PAGE -----------------------------
elif page == "Alert Management":
    st.markdown(
        '<div class="section-title">Alert Management</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-note">Evaluate current reference-location rainfall conditions, '
        'review persisted alerts, and manage their lifecycle.</div>',
        unsafe_allow_html=True,
    )
    st.warning(
        "Prototype only: these rules are illustrative, thresholds are not validated flood thresholds, "
        "and an alert does not confirm waterlogging. This is not an emergency-warning service."
    )

    with st.expander("Evaluate rainfall and create alerts", expanded=True):
        st.write(
            "This runs the existing live rainfall inference for the configured reference location. "
            "It does not use browser GPS or automatically send mobile notifications."
        )
        eval_col1, eval_col2 = st.columns(2)
        with eval_col1:
            alert_latitude = st.number_input(
                "Alert latitude", min_value=-90.0, max_value=90.0,
                value=17.3850, step=0.0001, format="%.5f",
                help="Defaults to a Hyderabad reference coordinate; edit if appropriate.",
            )
        with eval_col2:
            alert_longitude = st.number_input(
                "Alert longitude", min_value=-180.0, max_value=180.0,
                value=78.4867, step=0.0001, format="%.5f",
                help="These coordinates label the alert record; rainfall inference uses the configured reference endpoint.",
            )
        if st.button("Evaluate current rainfall and create alerts", key="evaluate_alerts", use_container_width=True):
            try:
                inference = get_live_rainfall_inference()
                payload = {
                    "rainfall_risk_level": inference.get(
                        "rainfall_risk_level", inference.get("risk_level", "LOW")
                    ),
                    "rainfall_rolling_3h_mm": inference.get(
                        "rainfall_rolling_3h_mm", inference.get("rainfall_3h_mm", 0)
                    ),
                    "rainfall_rolling_6h_mm": inference.get(
                        "rainfall_rolling_6h_mm", inference.get("rainfall_6h_mm", 0)
                    ),
                    "rainfall_rolling_24h_mm": inference.get(
                        "rainfall_rolling_24h_mm", inference.get("rainfall_24h_mm", 0)
                    ),
                    "unusual_rainfall_pattern": bool(
                        inference.get("unusual_rainfall_pattern", False)
                    ),
                    "anomaly_score": inference.get("anomaly_score"),
                    "interpretation": inference.get("interpretation", "live_rainfall_inference"),
                    "data_status": inference.get("data_status", "live_rainfall_inference"),
                    "location": {
                        "latitude": float(alert_latitude),
                        "longitude": float(alert_longitude),
                    },
                }
                result = evaluate_alerts(payload)
                get_alert_history.clear()
                st.session_state["last_alert_evaluation"] = result
                status = result.get("status", "EVALUATED")
                if status == "ALERT_CREATED":
                    st.success(f"Alert evaluation completed: {len(result.get('alerts', []))} alert(s) created.")
                elif status == "DUPLICATE_SUPPRESSED":
                    st.info("Matching active alerts already exist; duplicate creation was suppressed.")
                else:
                    st.success(f"Alert evaluation completed: {status}")
            except requests.HTTPError as exc:
                details = exc.response.text if exc.response is not None else str(exc)
                st.error(f"Alert evaluation failed: {details}")
            except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
                st.error(f"Could not evaluate alerts: {exc}")

        if st.session_state.get("last_alert_evaluation"):
            st.markdown("#### Latest evaluation response")
            st.json(st.session_state["last_alert_evaluation"])

    st.markdown('<div class="section-title">Persisted alerts</div>', unsafe_allow_html=True)
    refresh_col, filter_col = st.columns([1, 2])
    with refresh_col:
        if st.button("Refresh alert history", key="refresh_alert_history"):
            get_alert_history.clear()
            st.rerun()
    with filter_col:
        status_filter = st.selectbox(
            "Filter by status", ["ALL", "ACTIVE", "ACKNOWLEDGED", "RESOLVED"],
            key="alert_status_filter",
        )

    try:
        alert_response = get_alert_history(limit=100)
        alert_records = alert_response.get("records", [])
        alert_df = pd.DataFrame(alert_records)
        if not alert_df.empty:
            total_count = len(alert_df)
            active_count = int((alert_df.get("status", pd.Series(dtype=str)) == "ACTIVE").sum())
            acknowledged_count = int((alert_df.get("status", pd.Series(dtype=str)) == "ACKNOWLEDGED").sum())
            resolved_count = int((alert_df.get("status", pd.Series(dtype=str)) == "RESOLVED").sum())
            metric1, metric2, metric3, metric4 = st.columns(4)
            metric1.metric("Total alerts", total_count)
            metric2.metric("Active", active_count)
            metric3.metric("Acknowledged", acknowledged_count)
            metric4.metric("Resolved", resolved_count)

            shown_df = alert_df.copy()
            if status_filter != "ALL" and "status" in shown_df.columns:
                shown_df = shown_df[shown_df["status"].astype(str).str.upper() == status_filter]
            preferred = [
                "id", "created_at_utc", "updated_at_utc", "risk_level", "rule_key",
                "reason", "status", "latitude", "longitude", "rainfall_3h_mm",
                "rainfall_6h_mm", "rainfall_24h_mm", "anomaly_score", "data_status",
                "waterlogging_confirmed",
            ]
            visible = [col for col in preferred if col in shown_df.columns]
            st.dataframe(shown_df[visible], use_container_width=True, hide_index=True)
            st.download_button(
                "Download alert history as CSV",
                data=shown_df[visible].to_csv(index=False).encode("utf-8"),
                file_name="geosentinel_alert_history.csv",
                mime="text/csv",
            )

            st.markdown("#### Update alert status")
            editable_records = [
                record for record in alert_records
                if str(record.get("status", "")).upper() in {"ACTIVE", "ACKNOWLEDGED"}
            ]
            if editable_records:
                options = {
                    f"ID {record.get('id')} · {record.get('rule_key')} · {record.get('status')}": record
                    for record in editable_records
                }
                selected_label = st.selectbox("Select an alert", list(options.keys()), key="selected_alert_to_update")
                selected_record = options[selected_label]
                current_status = str(selected_record.get("status", "ACTIVE")).upper()
                allowed_statuses = ["ACKNOWLEDGED", "RESOLVED"] if current_status == "ACTIVE" else ["RESOLVED"]
                new_status = st.selectbox("New status", allowed_statuses, key=f"new_status_{selected_record.get('id')}")
                if st.button("Save alert status", key="save_alert_status"):
                    try:
                        updated = update_alert_status(selected_record["id"], new_status)
                        get_alert_history.clear()
                        st.success(f"Alert {updated.get('id')} status updated to {updated.get('status')}.")
                        st.rerun()
                    except requests.HTTPError as exc:
                        details = exc.response.text if exc.response is not None else str(exc)
                        st.error(f"Status update failed: {details}")
                    except requests.RequestException as exc:
                        st.error(f"Could not update alert status: {exc}")
            else:
                st.info("There are no ACTIVE or ACKNOWLEDGED alerts available for a status update.")
        else:
            st.info("No alerts have been recorded yet. Run an evaluation above to create prototype alerts.")
        st.caption(
            f"API data status: {alert_response.get('data_status', 'unavailable')} · "
            "Waterlogging confirmed: No. Alerts are monitoring signals, not verified flood events."
        )
    except (requests.RequestException, ValueError, TypeError) as exc:
        st.error(f"Alert history could not be loaded: {exc}")
        st.info("Confirm the FastAPI service is running and the alert endpoints are available in /docs.")

# ----------------------------- RAINFALL PAGE -----------------------------
elif page == "Rainfall Analytics":

    st.markdown('<div class="section-title">Rainfall Analytics</div>',

                unsafe_allow_html=True)

    st.markdown(

        f'<div class="section-note">Available history: {start_label} — {end_label}</div>',

        unsafe_allow_html=True,

    )



    if history.empty:

        st.warning("Rainfall history is unavailable.")

    else:

        start_date = history["observed_at"].min().date()

        end_date = history["observed_at"].max().date()



        date_range = st.date_input(

            "Analysis period",

            value=(start_date, end_date),

            min_value=start_date,

            max_value=end_date,

        )



        selected = history

        if isinstance(date_range, (tuple, list)) and len(date_range) == 2:

            start, end = date_range

            selected = history[

                history["observed_at"].dt.date.between(start, end)

            ]



        selected_anomalies = (

            int(selected["anomaly_flag"].sum())

            if len(selected) and "anomaly_flag" in selected

            else 0

        )



        a, b, c = st.columns(3)

        a.metric("Observations", f"{len(selected):,}")

        b.metric("Unusual patterns", f"{selected_anomalies:,}")

        c.metric(

            "Anomaly rate",

            f"{selected_anomalies / len(selected) * 100:.2f}%"

            if len(selected) else "—",

        )



        if len(selected) and "precipitation_mm" in selected:

            fig = go.Figure()

            fig.add_trace(

                go.Scatter(

                    x=selected["observed_at"],

                    y=selected["precipitation_mm"],

                    mode="lines",

                    name="Hourly rainfall",

                    line=dict(color="#20E0D0", width=1.6),

                    fill="tozeroy",

                    fillcolor="rgba(32,224,208,.10)",

                )

            )



            if "anomaly_flag" in selected:

                unusual = selected[selected["anomaly_flag"]]

                fig.add_trace(

                    go.Scatter(

                        x=unusual["observed_at"],

                        y=unusual["precipitation_mm"],

                        mode="markers",

                        name="Unusual pattern",

                        marker=dict(color="#F45B78", size=6),

                    )

                )



            fig = make_chart_layout(fig, 360)

            fig.update_yaxes(title_text="Rainfall (mm)")

            st.plotly_chart(fig, use_container_width=True,

                            config={"displayModeBar": False})



        rolling = [

            col for col in [

                "rainfall_rolling_3h_mm",

                "rainfall_rolling_6h_mm",

                "rainfall_rolling_24h_mm",

            ] if col in selected.columns

        ]



        if len(selected) and rolling:

            fig = go.Figure()

            colors = ["#35BFFF", "#9B87F5", "#24D6A4"]



            for col, color in zip(rolling, colors):

                fig.add_trace(

                    go.Scatter(

                        x=selected["observed_at"],

                        y=selected[col],

                        name=col.replace("rainfall_rolling_", "").replace("_mm", ""),

                        mode="lines",

                        line=dict(color=color, width=1.5),

                    )

                )



            fig = make_chart_layout(fig, 330)

            fig.update_yaxes(title_text="Rainfall (mm)")

            st.plotly_chart(fig, use_container_width=True,

                            config={"displayModeBar": False})



        if len(selected) and "anomaly_score" in selected:

            st.markdown("Most unusual observations")

            display = selected.sort_values("anomaly_score").head(20)

            columns = [

                col for col in [

                    "observed_at", "precipitation_mm",

                    "rainfall_rolling_3h_mm", "rainfall_rolling_6h_mm",

                    "rainfall_rolling_24h_mm", "anomaly_score", "anomaly_flag",

                ] if col in display.columns

            ]

            st.dataframe(

                display[columns],

                use_container_width=True,

                hide_index=True,

            )



        st.caption(

            "Isolation Forest anomalies describe unusual rainfall patterns, "

            "not waterlogging probability."

        )
# ----------------------------- GEOSPATIAL PAGE -----------------------------
elif page == "Geospatial Intelligence":

    st.markdown('<div class="section-title">Geospatial Intelligence</div>',

                unsafe_allow_html=True)

    st.warning(

        "These are historical mapped locations. They are not independently "

        "verified or live/predicted flooding areas."

    )



    if not hotspot_features:

        st.info("No hotspot polygons are available.")

    else:

        coords = []

        for feature in hotspot_features:

            geometry = feature.get("geometry") or {}

            if geometry.get("type") == "Polygon":

                for ring in geometry.get("coordinates", []):

                    coords.extend(

                        point[:2] for point in ring if len(point) >= 2

                    )



        if coords:

            lon = sum(p[0] for p in coords) / len(coords)

            lat = sum(p[1] for p in coords) / len(coords)



            map_obj = folium.Map(

                location=[lat, lon],

                zoom_start=12,

                tiles="OpenStreetMap",

            )



            folium.GeoJson(

                geojson,

                name="Historical grid cells",

                style_function=lambda feature: {

                    "color": "#20E0D0",

                    "weight": 1.5,

                    "fillColor": "#087F8C",

                    "fillOpacity": 0.38,

                },

                tooltip=folium.GeoJsonTooltip(

                    fields=["grid_id", "mapped_location_count", "record_type"],

                    aliases=["Grid ID", "Mapped locations", "Record type"],

                ),

            ).add_to(map_obj)



            folium.LayerControl().add_to(map_obj)

            st_folium(

                map_obj,

                height=620,

                use_container_width=True,

                key="geospatial_map",

            )



        st.markdown("Mapped grid cells")

        st.dataframe(

            pd.DataFrame(

                [

                    {

                        "Grid ID": (f.get("properties") or {}).get("grid_id"),

                        "Mapped locations": (

                            f.get("properties") or {}

                        ).get("mapped_location_count"),

                        "Record type": (

                            f.get("properties") or {}

                        ).get("record_type"),

                    }

                    for f in hotspot_features

                ]

            ),

            use_container_width=True,

            hide_index=True,

        )
# ----------------------------- STATUS PAGE -----------------------------
elif page == "Data & Model Status":

    st.markdown('<div class="section-title">Data & Model Status</div>',

                unsafe_allow_html=True)



    a, b = st.columns(2)



    with a:

        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)

        st.markdown('<div class="panel-title">API Service Health</div>',

                    unsafe_allow_html=True)

        st.json(health)

        st.markdown("</div>", unsafe_allow_html=True)



    with b:

        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)

        st.markdown('<div class="panel-title">Latest Rainfall Response</div>',

                    unsafe_allow_html=True)

        st.json(rainfall)

        st.markdown("</div>", unsafe_allow_html=True)



    st.markdown("Geospatial provenance")

    st.json({

        key: hotspot_response.get(key)

        for key in [

            "data_status", "is_flooding_prediction", "independently_verified"

        ]

    })



    st.markdown("Current platform limitations")

    st.markdown(

        """

        - Historical rainfall currently covers June–August 2025.

        - Rainfall observations represent one reference location.

        - Mapped locations have no verified occurrence timestamps or severity.

        - Isolation Forest detects unusual rainfall, not confirmed flooding.

        - Live weather, live GPS, mobile alerts, and an AI agent are not yet connected.

        """

    )
# ----------------------------- FOOTER -----------------------------
st.divider()

st.markdown(
    """
    <div style="text-align:center; color:#7897B2; font-size:10px; letter-spacing:1px; padding:8px;">
        <div style="font-weight:700; margin-bottom:5px;">
            GEOSENTINEL AI · ENVIRONMENTAL INTELLIGENCE
        </div>
        <div>
            Historical prototype · Not an emergency warning service
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
