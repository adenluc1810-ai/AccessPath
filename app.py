import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from streamlit_folium import st_folium

# Streamlit Page Config
st.set_page_config(page_title="AccessPath", layout="wide")

st.title("♿ AccessPath: Uncertainty-Aware Pedestrian Route Planner")
st.write("Comparing **Standard Shortest Path (Red)** vs **Accessibility-Weighted Path (Green)**.")

# OSMnx Speed & Connection Optimization
ox.settings.user_agent = "AccessPathPedestrianApp/1.0"
ox.settings.timeout = 180
ox.settings.use_cache = True

# Fast Cached Map Graph Fetcher
@st.cache_data(show_spinner=False, ttl=3600)
def load_map_graph(lat, lon, radius):
    return ox.graph_from_point((lat, lon), dist=radius, network_type="walk", truncate_by_edge=True)

# Sidebar Configuration
st.sidebar.header("⚙️ Routing Settings")
lat = st.sidebar.number_input("Center Latitude", value=13.0827, format="%.4f")
lon = st.sidebar.number_input("Center Longitude", value=80.2707, format="%.4f")
radius = st.sidebar.slider("Map Radius (meters)", min_value=300, max_value=1000, value=500, step=100)

w_barrier = st.sidebar.slider("Barrier Penalty Weight (Stairs/Curb)", 50, 500, 200)
w_uncertainty = st.sidebar.slider("Uncertainty Penalty Weight (Missing Tags)", 0, 100, 20)

# Load Graph Data
with st.spinner("⚡ Fetching OpenStreetMap Network..."):
    try:
        G = load_map_graph(lat, lon, radius)
        nodes = list(G.nodes())
    except Exception as e:
        st.error("OpenStreetMap network load aagala. Please refresh or try again.")
        st.stop()

# Custom Accessibility Cost Function
def custom_cost(u, v, data):
    edge_data = data if isinstance(data, dict) else data[0] if isinstance(data, list) else {}
    length = edge_data.get('length', 1.0)
    highway = edge_data.get('highway', '')
    wheelchair = edge_data.get('wheelchair', 'unknown')
    incline = edge_data.get('incline', None)

    cost = length

    if highway == 'steps' or wheelchair == 'no':
        cost += w_barrier
    if incline in ['steep', 'up', 'down']:
        cost += w_barrier * 0.5

    if wheelchair == 'unknown':
        cost += w_uncertainty

    return cost

# Route Calculation and Display
if len(nodes) >= 2:
    orig_node = nodes[0]
    dest_node = nodes[-1]

    # Calculate Paths
    shortest_path = nx.shortest_path(G, orig_node, dest_node, weight='length')
    accessible_path = nx.shortest_path(G, orig_node, dest_node, weight=custom_cost)

    # Coords
    shortest_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in shortest_path]
    accessible_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in accessible_path]
    
    orig_pos = (G.nodes[orig_node]['y'], G.nodes[orig_node]['x'])
    dest_pos = (G.nodes[dest_node]['y'], G.nodes[dest_node]['x'])

    # Create Map with Clean Google-style Tile (CartoDB Positron)
    m = folium.Map(location=orig_pos, zoom_start=16, tiles="CartoDB positron")

    # Add Google Maps standard Layer option
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attr='Google Maps',
        name='Google Maps',
        overlay=False,
        control=True
    ).add_to(m)

    # Add Google Satellite Layer option
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)

    # Start and Destination Markers
    folium.Marker(
        orig_pos, 
        popup="<b>Start Point</b>", 
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)
    
    folium.Marker(
        dest_pos, 
        popup="<b>Destination</b>", 
        icon=folium.Icon(color="red", icon="flag")
    ).add_to(m)

    # Plot Routes with Google Maps thick style
    folium.PolyLine(shortest_coords, color="#EA4335", weight=7, opacity=0.8, tooltip="Standard Shortest Path").add_to(m)
    folium.PolyLine(accessible_coords, color="#34A853", weight=7, opacity=0.9, tooltip="Accessible Path").add_to(m)

    # Auto-Zoom
    all_coords = shortest_coords + accessible_coords
    m.fit_bounds(all_coords)

    # Layer Control (Top Right corner-la Google Map vs Satellite choose பண்ணலாம்)
    folium.LayerControl().add_to(m)

    # Display Map
    st_folium(m, width="100%", height=550)
else:
    st.warning("Not enough nodes found. Sidebar-la Radius-a increase pannunga.")