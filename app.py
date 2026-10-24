import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from streamlit_folium import st_folium

# Streamlit Page Config
st.set_page_config(page_title="AccessPath", layout="wide")

st.title("♿ AccessPath: Uncertainty-Aware Pedestrian Route Planner")
st.write("Comparing **Standard Shortest Path (Red)** vs **Accessibility-Weighted Path (Green)**.")

# OSMnx Speed & Accuracy Optimization
ox.settings.user_agent = "AccessPathPedestrianApp/1.0"
ox.settings.timeout = 180
ox.settings.use_cache = True

# Accurate Cached Map Graph Fetcher (Fixes walking on water issue)
@st.cache_data(show_spinner=False, ttl=3600)
def load_map_graph(lat, lon, radius):
    return ox.graph_from_point((lat, lon), dist=radius, network_type="walk", truncate_by_edge=False)

# Sidebar Configuration
st.sidebar.header("⚙️ Routing Settings")
lat = st.sidebar.number_input("Center Latitude", value=13.0827, format="%.4f")
lon = st.sidebar.number_input("Center Longitude", value=80.2707, format="%.4f")
radius = st.sidebar.slider("Map Radius (meters)", min_value=300, max_value=1000, value=500, step=100)

w_barrier = st.sidebar.slider("Barrier Penalty Weight (Stairs/Curb)", 50, 500, 200)
w_uncertainty = st.sidebar.slider("Uncertainty Penalty Weight (Missing Tags)", 0, 100, 20)

# Load Graph Data
with st.spinner("⚡ Fetching Accurate Street Network..."):
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

    # Barrier Penalties
    if highway == 'steps' or wheelchair == 'no':
        cost += w_barrier
    if incline in ['steep', 'up', 'down']:
        cost += w_barrier * 0.5

    # Uncertainty Penalties
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

    # Coords for Route Visualization
    shortest_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in shortest_path]
    accessible_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in accessible_path]
    
    orig_pos = (G.nodes[orig_node]['y'], G.nodes[orig_node]['x'])
    dest_pos = (G.nodes[dest_node]['y'], G.nodes[dest_node]['x'])

    # Esri World Street Map Tiles (Google Maps style - HD Street & Place names clear-a theryum, No API Key)
    m = folium.Map(
        location=orig_pos, 
        zoom_start=16, 
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Street Map"
    )

    # Start and Destination Markers with Popup Place Info
    folium.Marker(
        orig_pos, 
        popup="📍 <b>Start Location</b>", 
        tooltip="Start Point",
        icon=folium.Icon(color="blue", icon="play")
    ).add_to(m)
    
    folium.Marker(
        dest_pos, 
        popup="🏁 <b>Destination Location</b>", 
        tooltip="Destination",
        icon=folium.Icon(color="red", icon="flag")
    ).add_to(m)

    # Plot Routes (Red = Shortest Path, Green = Accessible Path)
    folium.PolyLine(shortest_coords, color="#EA4335", weight=6, opacity=0.8, tooltip="Standard Shortest Path (Red)").add_to(m)
    folium.PolyLine(accessible_coords, color="#34A853", weight=6, opacity=0.9, tooltip="Accessible Path (Green)").add_to(m)

    # Auto-Zoom to exact route bounds
    all_coords = shortest_coords + accessible_coords
    m.fit_bounds(all_coords)

    # Display Map
    st_folium(m, width="100%", height=550)
else:
    st.warning("Not enough nodes found. Sidebar-la Radius-a increase pannunga.")