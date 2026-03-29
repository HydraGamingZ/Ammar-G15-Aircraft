import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import datetime
import time
import os
from folium import plugins
from folium.plugins import HeatMap

# 1. UI & THEME
st.set_page_config(
    page_title="Perak Flight Tracker",
    page_icon="✈️",
    layout="wide"
)

st.markdown("""
<style>

/* main background */
.stApp {
    background-color: #0e1117;
    font-family: 'Segoe UI', sans-serif;
}

/* glass effect cards */
.glass-card {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 15px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    margin-bottom: 10px;
}

/* big metric number */
.metric-hero {
    font-size: 28px;
    font-weight: bold;
    color: #4FC3F7;
    margin: 0;
}

/* small label */
.metric-sub {
    font-size: 11px;
    color: rgba(255,255,255,0.6);
    text-transform: uppercase;
}

</style>
""", unsafe_allow_html=True)

# 2. DATA ENGINE (FIXED DIRECTORY PATH)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "perak_flights.csv")

try:
    if os.path.exists(CSV_PATH) and os.path.getsize(CSV_PATH) > 0:
        data = pd.read_csv(CSV_PATH)
        if 'Timestamp' in data.columns:
            data['Timestamp'] = pd.to_datetime(data['Timestamp'], errors='coerce')
            data = data.dropna(subset=['Timestamp']) 
    else:
        data = pd.DataFrame(columns=['Timestamp', 'Aircraft_ID', 'Flight_Name', 'Latitude', 'Longitude', 'Altitude'])
except Exception as e:
    st.error(f"⚠️ Database Error: {e}") 
    data = pd.DataFrame(columns=['Timestamp', 'Aircraft_ID', 'Flight_Name', 'Latitude', 'Longitude', 'Altitude'])

# 3. SIDEBAR (Clock, Search, Heatmap, Toggle & DEVELOPERS)
st.sidebar.markdown("<h2 style='color: #01579B;'>🕒 Live Master Clock</h2>", unsafe_allow_html=True)
clock_placeholder = st.sidebar.empty()
clock_placeholder.code(datetime.datetime.now().strftime("%d %B %Y | %H:%M:%S"))

st.sidebar.markdown("---")
# THE PAUSE/LIVE TOGGLE (Improvisation #2)
is_live = st.sidebar.toggle("🟢 Live Auto-Refresh", value=True, help="Turn off to pause the screen and analyze data.")

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Database Query Engine")
search_term = st.sidebar.text_input("Search Flight/ICAO:", "").strip().upper()

st.sidebar.markdown("---")
st.sidebar.subheader("📍 Airport Inference")
show_heatmap = st.sidebar.checkbox("Activate Inference Heatmap", value=False)

# --- SUBTLE DEVELOPER SECTION ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 👨‍💻 Project Developers")
st.sidebar.markdown("""
<div style="font-size: 13px; color: #444; line-height: 1.6;">
    • <b>Ammar Mustaqim Bin Mohamad Shamsul Akhmar</b> <span style="color:#777;">(22005646)</span><br>
    
</div>
""", unsafe_allow_html=True)

# 4. HEADER METRICS
st.markdown("<h1 style='color: #01579B;'>🛰️ Perak Aviation Intelligence Control</h1>", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="glass-card"><p class="metric-sub">Total Packets</p><p class="metric-hero">{len(data)}</p></div>', unsafe_allow_html=True)
with c2:
    unique = data['Aircraft_ID'].nunique() if not data.empty else 0
    st.markdown(f'<div class="glass-card"><p class="metric-sub">Unique Assets</p><p class="metric-hero">{unique}</p></div>', unsafe_allow_html=True)
with c3:
    if len(data) > 1:
        diff = data.iloc[-1]['Altitude'] - data.iloc[-2]['Altitude']
        trend = "⬆️ CLIMB" if diff > 5 else ("⬇️ DESCENT" if diff < -5 else "➡️ CRUISE")
        st.markdown(f'<div class="glass-card"><p class="metric-sub">Active Trend</p><p class="metric-hero" style="font-size:18px">{trend}</p></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="glass-card"><p class="metric-sub">Active Trend</p><p class="metric-hero">WAITING...</p></div>', unsafe_allow_html=True)
with c4:
    st.markdown(f'<div class="glass-card"><p class="metric-sub">Target Region</p><p class="metric-hero">PERAK</p></div>', unsafe_allow_html=True)

# Filtering Logic
if search_term and not data.empty:
    filtered_data = data[(data['Flight_Name'].astype(str).str.contains(search_term)) | (data['Aircraft_ID'].astype(str).str.contains(search_term))]
else:
    filtered_data = data

# 5. SIDE-BY-SIDE SPLIT (Map on Left, Analytics on Right)
st.markdown("---")
col_map, col_graph = st.columns([1.3, 1]) 

with col_map:
    st.subheader("📍 Live Geospatial Tracking")
    m = folium.Map(location=[4.75, 101.00], zoom_start=8.2, tiles=None)

    folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                     attr='Esri Satellite', name="Satellite High-Res").add_to(m)
    folium.TileLayer(tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                     attr='&copy; OpenStreetMap', name="Standard Map").add_to(m)

    border_coords = [[3.50, 100.20], [3.50, 101.80], [6.00, 101.80], [6.00, 100.20], [3.50, 100.20]]
    folium.PolyLine(border_coords, color="#01579B", weight=5, opacity=1.0, dash_array='10, 10').add_to(m)

    if not filtered_data.empty:
        # Ghost Plane Fix
        recent_time = filtered_data['Timestamp'].max() - pd.Timedelta(minutes=15)
        live_planes = filtered_data[filtered_data['Timestamp'] >= recent_time]
        
        # THE SNAIL TRAIL (Improvisation #1)
        for flight_id, flight_history in live_planes.groupby('Aircraft_ID'):
            latest_row = flight_history.tail(1).iloc[0]
            color = 'orange' if latest_row['Altitude'] < 2500 else '#00FF00'
            
            if len(flight_history) > 1:
                trail_coords = flight_history[['Latitude', 'Longitude']].values.tolist()
                folium.PolyLine(trail_coords, color=color, weight=2, opacity=0.5, dash_array='5, 5').add_to(m)
                
            folium.CircleMarker(
                location=[latest_row['Latitude'], latest_row['Longitude']], 
                radius=9, color=color, fill=True, fill_opacity=0.9,
                popup=f"<b>{latest_row['Flight_Name']}</b>"
            ).add_to(m)

    if show_heatmap and not data.empty:
        low_alt = data[data['Altitude'] < 1200][['Latitude', 'Longitude']]
        if not low_alt.empty:
            HeatMap(low_alt.values.tolist(), radius=15, blur=10).add_to(m)

    folium.LayerControl().add_to(m)
    plugins.Fullscreen().add_to(m)
    
    st_folium(m, width=800, height=520, use_container_width=True, returned_objects=[])

with col_graph:
    st.subheader("📈 Aviation Analytics")
    
    st.write("✈️ **1. Current Altitude Profile (Time-Series)**")
    if not filtered_data.empty:
        st.line_chart(filtered_data, x='Timestamp', y='Altitude', height=140)
    else:
        st.caption("Waiting for flight data...")

    st.write("📊 **2. Aircraft Frequency (Hits in Database)**")
    if not data.empty:
        st.bar_chart(data['Flight_Name'].value_counts().head(5), height=140)
    else:
        st.caption("Waiting for flight data...")
        
    st.write("🏔️ **3. Maximum Altitude by Flight (m)**")
    if not data.empty:
        max_alt = data.groupby('Flight_Name')['Altitude'].max().head(5)
        st.area_chart(max_alt, height=140)
    else:
        st.caption("Waiting for flight data...")

# 6. DATABASE SUMMARY & TABLE
st.markdown("---")
st.subheader("📊 Database Insight Panel")
if not data.empty:
    # Changed to 4 columns to fit the new Vertical Speed metric cleanly!
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        low = data.loc[data['Altitude'].idxmin()]
        st.info(f"🚁 **Lowest Asset:** {low['Flight_Name']} ({low['Altitude']}m)")
    with s2:
        top_asset = data['Flight_Name'].value_counts().idxmax()
        st.success(f"📈 **Top Asset:** {top_asset}")
    with s3:
        st.warning(f"✅ **DB Integrity:** {len(data)} Vectors")
    with s4:
        # VERTICAL SPEED CALCULATOR (Improvisation #3)
        latest_aircraft_id = data.sort_values(by='Timestamp').iloc[-1]['Aircraft_ID']
        plane_history = data[data['Aircraft_ID'] == latest_aircraft_id].sort_values(by='Timestamp')
        
        if len(plane_history) > 1:
            recent_2 = plane_history.tail(2)
            alt_diff = recent_2.iloc[-1]['Altitude'] - recent_2.iloc[0]['Altitude']
            time_diff = (recent_2.iloc[-1]['Timestamp'] - recent_2.iloc[0]['Timestamp']).total_seconds() / 60
            
            if time_diff > 0:
                vertical_speed = alt_diff / time_diff
                st.info(f"🚀 **V-Speed:** {vertical_speed:.0f} m/min")
            else:
                st.info("🚀 **V-Speed:** N/A")
        else:
            st.info("🚀 **V-Speed:** Calculating...")

st.subheader("📄 Historical State Vector Database")
if not filtered_data.empty:
    st.dataframe(filtered_data.sort_values(by='Timestamp', ascending=False), use_container_width=True, hide_index=True)
else:
    st.caption("No historical data to display yet.")
    
st.download_button("📩 Download IoT Database (CSV)", data.to_csv(index=False).encode('utf-8') if not data.empty else "", "perak_iot_report.csv")

# 7. REFRESH
if is_live:
    time.sleep(1)
    st.rerun()