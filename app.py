import streamlit as st
import ee
import folium
import pandas as pd
import plotly.express as px
from streamlit_folium import st_folium

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="Global Air Quality WebGIS",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌍 Global Air Quality Monitoring WebGIS")
st.markdown("### Sentinel-5P TROPOMI Atmospheric NO₂ Spatial Analytics Platform")

# --- Google Earth Engine Initialization ---
PROJECT_ID = 'flood-extent-mapping-punjab' # Replace with your GCP project ID

@st.cache_resource
def init_gee():
    try:
        ee.Initialize(project=PROJECT_ID)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJECT_ID)

init_gee()

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Spatial Analysis Parameters")

target_city = st.sidebar.selectbox(
    "Select Focus Urban Corridor",
    ["Lahore", "Gujranwala", "Faisalabad", "Amritsar"]
)

buffer_dist = st.sidebar.slider("Spatial Buffer Radius (km)", 5, 50, 15)

city_coords = {
    'Lahore': [74.3587, 31.5204],
    'Gujranwala': [74.1883, 32.1617],
    'Faisalabad': [73.0791, 31.4187],
    'Amritsar': [74.8723, 31.6340]
}

# --- Spatial Analytics Pipeline ---
coords = city_coords[target_city]
roi = ee.Geometry.Point(coords).buffer(buffer_dist * 1000)

s5p_no2 = (ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_NO2')
           .filterDate('2025-01-01', '2025-06-01')
           .select('tropospheric_NO2_column_number_density')
           .mean()
           .clip(roi))

vis_params = {
    'min': 0.00002,
    'max': 0.0002,
    'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']
}

# --- Map Rendering ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Satellite NO₂ Column Density: {target_city}")
    m = folium.Map(location=[coords[1], coords[0]], zoom_start=10, tiles='cartodbdarkmatter')
    map_id = ee.Image(s5p_no2).getMapId(vis_params)
    
    folium.TileLayer(
        tiles=map_id['tile_fetcher'].url_format,
        attr='ESA / Google Earth Engine',
        name='Sentinel-5P NO2'
    ).add_to(m)
    
    st_folium(m, width=700, height=500)

with col2:
    st.subheader("Regional Summary")
    st.metric(label="Selected Buffer Radius", value=f"{buffer_dist} km")
    st.info("Sentinel-5P TROPOMI sensor collects atmospheric tropospheric vertical column density of NO₂ measured in mol/m².")
# Updated GEE Initialization inside app.py
PROJECT_ID = 'flood-extent-mapping-punjab'

@st.cache_resource
def init_gee():
    try:
        ee.Initialize(project=PROJECT_ID)
        st.sidebar.success("✅ Connected to Google Earth Engine")
    except Exception as e:
        st.sidebar.error("❌ GEE Connection Failed. Authenticate in Colab first.")
        st.error(f"Earth Engine Error: {e}")

init_gee()
