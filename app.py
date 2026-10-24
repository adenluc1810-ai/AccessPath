import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from streamlit_folium import st_folium

# Streamlit Page Configuration
st.set_page_config(page_title="AccessPath - Accessibility Routing", layout="wide")

st.title("♿ AccessPath: Uncertainty-Aware Pedestrian Route Planner")
st.markdown("Comparing **Standard Shortest Path** vs **Accessibility & Uncertainty-Weighted Path**.")

# OSMnx Settings & Cache
ox.settings.use_cache = True
ox.settings.user_agent = "AccessPath_Streamlit_App_v1"

@st.cache_data
def load_map_graph(lat, lon, radius):
    # Download pedestrian walking network
    return ox.graph_from_point((lat, lon), dist=radius, network_type="walk")

# Sidebar Configuration
st.sidebar.header("⚙️ Routing Settings")
lat = st.sidebar.number_input("Center Latitude", value=12.9915, format="%.4f")
lon = st.sidebar.number_input("Center Longitude", value=80.2337, format="%.4f")
radius = st.sidebar.slider("Map Radius (meters)", min_value=300, max_value=1000, value=500, step=100)

w_barrier = st.sidebar.slider("Barrier Penalty Weight (Stairs/Curb)", 50, 500, 200)
w_uncertainty = st.sidebar.slider("Uncertainty Penalty Weight (Missing Tags)", 0, 100, 20)

with st.spinner("Loading OpenStreetMap Network..."):
    G = load_map_graph(lat, lon, radius)

nodes = list(G.nodes())

# Routing Function
def custom_cost(u, v, data):
    edge_data = data if isinstance(data, dict) else data[0] if isinstance(data, list) else {}
    length = edge_data.get('length', 1.0)
    highway = edge_data.get('highway', '')
    wheelchair = edge_data.get('wheelchair', 'unknown')
    incline = edge_data.get('incline', None)
    
    penalty = 0.0
    if highway == 'steps' or wheelchair == 'no':
        penalty += w_barrier
    if wheelchair == 'unknown' or incline is None:
        penalty += w_uncertainty
        
    return length + penalty

# Select Origin and Destination
st.subheader("📍 Route Selection")
col1, col2 = st.columns(2)
with col1:
    origin_idx = st.number_input("Origin Node Index", min_value=0, max_value=len(nodes)-1, value=0)
with col2:
    dest_idx = st.number_input("Destination Node Index", min_value=0, max_value=len(nodes)-1, value=min(20, len(nodes)-1))

origin_node = nodes[origin_idx]
dest_node = nodes[dest_idx]

if st.button("🚀 Calculate Routes"):
    # 1. Baseline Route
    base_path = nx.dijkstra_path(G, origin_node, dest_node, weight='length')
    base_dist = nx.dijkstra_path_length(G, origin_node, dest_node, weight='length')
    
    # 2. AccessPath Route
    access_path = nx.astar_path(G, origin_node, dest_node, weight=custom_cost)
    access_dist = sum(G.get_edge_data(access_path[i], access_path[i+1])[0].get('length', 0) for i in range(len(access_path)-1))
    
    detour = access_dist / base_dist if base_dist > 0 else 1.0
    
    # Display Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Standard Shortest Distance", f"{round(base_dist, 1)} m")
    m2.metric("AccessPath Accessible Distance", f"{round(access_dist, 1)} m")
    m3.metric("Detour Factor", f"{round(detour, 2)} x")
    
    # Render Folium Map
    m = folium.Map(location=[lat, lon], zoom_start=16)
    
    # Draw Baseline Path (Red Dashed Line)
    base_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in base_path]
    folium.PolyLine(base_coords, color="red", weight=4, opacity=0.7, popup="Standard Shortest Path", tooltip="Standard Path").add_to(m)
    
    # Draw AccessPath (Blue Solid Line)
    access_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in access_path]
    folium.PolyLine(access_coords, color="blue", weight=5, opacity=0.9, popup="AccessPath (Accessible)", tooltip="Accessible Path").add_to(m)
    
    # Markers
    folium.Marker(base_coords[0], popup="Origin", icon=folium.Icon(color="green")).add_to(m)
    folium.Marker(base_coords[-1], popup="Destination", icon=folium.Icon(color="black")).add_to(m)
    
    st_folium(m, width=900, height=500)