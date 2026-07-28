import streamlit as st
import ee
import folium
import pandas as pd
import plotly.express as px
from streamlit_folium import st_folium

# --- 1. Streamlit Page Configuration ---
st.set_page_config(
    page_title="Global Air Quality WebGIS",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Google Earth Engine Initialization ---
PROJECT_ID = 'flood-extent-mapping-punjab'  # Your GCP Project ID

@st.cache_resource
def init_gee():
    try:
        ee.Initialize(project=PROJECT_ID)
        return True, "Successfully connected to Google Earth Engine!"
    except Exception as e:
        return False, str(e)

gee_ok, gee_msg = init_gee()

# --- 3. Header & Title Banner ---
st.title("🌍 Global Air Quality Monitoring WebGIS Dashboard")
st.markdown("### High-Resolution Sentinel-5P TROPOMI Atmospheric NO₂ Spatial Analytics")

# Stop execution gracefully if GEE is not authenticated
if not gee_ok:
    st.error(f"⚠️ **Earth Engine Connection Failed**: {gee_msg}")
    st.info("👉 **How to fix:** Run `ee.Authenticate()` inside a Colab notebook cell first to authenticate your session!")
    st.stop()

# --- 4. Sidebar Controls & Settings ---
st.sidebar.header("⚙️ Spatial Analysis Settings")

city_coords = {
    'Lahore': [74.3587, 31.5204],
    'Gujranwala': [74.1883, 32.1617],
    'Faisalabad': [73.0791, 31.4187],
    'Amritsar': [74.8723, 31.6340]
}

target_city = st.sidebar.selectbox("Select Target City / Corridor", list(city_coords.keys()))
buffer_dist = st.sidebar.slider("Spatial Buffer Radius (km)", 5, 50, 15)

st.sidebar.markdown("---")
st.sidebar.info("""
**Dataset Details:**
* **Satellite / Sensor:** ESA Sentinel-5P TROPOMI
* **Analyzed Molecule:** Tropospheric NO₂ Column Density
* **Measurement Unit:** µmol/m² (Micromoles per m²)
* **Timeframe:** Jan 2025 – Jun 2025 Mean
""")

# --- 5. Data Processing Backend ---
coords = city_coords[target_city]
roi = ee.Geometry.Point(coords).buffer(buffer_dist * 1000)

start_date = '2025-01-01'
end_date = '2025-06-01'

# Query Sentinel-5P Collection
s5p_no2_col = (ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_NO2')
               .filterDate(start_date, end_date)
               .select('tropospheric_NO2_column_number_density'))

s5p_mean = s5p_no2_col.mean()
s5p_clipped = s5p_mean.clip(roi)

# Thermal Palette Parameters
vis_params = {
    'min': 0.00002,
    'max': 0.0002,
    'palette': ['black', 'blue', 'purple', 'cyan', 'green', 'yellow', 'red']
}

# --- 6. Application Layout (Map & Dynamic Chart) ---
col1, col2 = st.columns([1.8, 1.2])

# Left Column: Interactive Map Render
with col1:
    st.subheader(f"🗺️ Spatial Layer: {target_city} ({buffer_dist} km Buffer)")
    
    # Base dark matter tile map
    m = folium.Map(location=[coords[1], coords[0]], zoom_start=10, tiles='cartodbdarkmatter')
    
    # Fetch Earth Engine tile URL
    map_id = ee.Image(s5p_clipped).getMapId(vis_params)
    
    folium.TileLayer(
        tiles=map_id['tile_fetcher'].url_format,
        attr='ESA / Google Earth Engine',
        name='Sentinel-5P NO₂ Layer',
        overlay=True,
        control=True
    ).add_to(m)
    
    folium.LayerControl().add_to(m)
    st_folium(m, width="100%", height=520)

# Right Column: Multi-City Spatial Query Analytics
with col2:
    st.subheader("📊 Multi-City Zonal Analytics")
    st.write("Executing real-time spatial buffer operations across regional hubs...")
    
    city_summary = []
    
    with st.spinner("Computing regional atmospheric stats..."):
        for name, c_coords in city_coords.items():
            c_point = ee.Geometry.Point(c_coords)
            c_buffer = c_point.buffer(buffer_dist * 1000)
            
            # Execute zonal statistical reduction
            stats = s5p_mean.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=c_buffer,
                scale=1000,
                maxPixels=1e9
            ).get('tropospheric_NO2_column_number_density')
            
            val = stats.getInfo() if stats else 0
            city_summary.append({
                'City': name,
                'NO2_umol_m2': val * 1e6 if val else 0  # Convert to µmol/m²
            })

    df_summary = pd.DataFrame(city_summary)

    # Plotly Bar Chart Render
    fig = px.bar(
        df_summary,
        x='City',
        y='NO2_umol_m2',
        color='NO2_umol_m2',
        color_continuous_scale='Reds',
        title='<b>Mean NO₂ Concentration Comparison</b>',
        labels={'NO2_umol_m2': 'Mean NO₂ (µmol/m²)', 'City': 'Urban Center'},
        template='plotly_dark'
    )

    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="#12141C",
        plot_bgcolor="#1E2230",
        height=350
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # Target Metric Display
    selected_val = df_summary[df_summary['City'] == target_city]['NO2_umol_m2'].values[0]
    st.metric(
        label=f"Selected Urban Buffer Density ({target_city})",
        value=f"{selected_val:.2f} µmol/m²"
    )
