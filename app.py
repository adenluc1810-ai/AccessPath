import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from streamlit_folium import st_folium

# Streamlit Page Config
st.set_page_config(page_title="AccessPath", layout="wide")

st.title("♿ AccessPath: Uncertainty-Aware Pedestrian Route Planner")
st.write("Comparing **Standard Shortest Path** vs **Accessibility & Uncertainty-Weighted Path**.")

# Step 1: User-Agent and Timeout for OSMnx (Prevents Connection Errors)
ox.settings.user_agent = "AccessPathPedestrianApp/1.0"
ox.settings.timeout = 180

# Step 2: Cached Map Loading Function
@st.cache_data(show_spinner="Downloading street network...")
def load_map_graph(lat, lon, radius):
    return ox.graph_from_point((lat, lon), dist=radius, network_type="walk")

# Step 3: Sidebar Configuration
st.sidebar.header("⚙️ Routing Settings")
lat = st.sidebar.number_input("Center Latitude", value=12.9915, format="%.4f")
lon = st.sidebar.number_input("Center Longitude", value=80.2337, format="%.4f")
radius = st.sidebar.slider("Map Radius (meters)", min_value=300, max_value=1000, value=500, step=100)

w_barrier = st.sidebar.slider("Barrier Penalty Weight (Stairs/Curb)", 50, 500, 200)
w_uncertainty = st.sidebar.slider("Uncertainty Penalty Weight (Missing Tags)", 0, 100, 20)

# Step 4: Load Graph Data
with st.spinner("Loading OpenStreetMap Network..."):
    G = load_map_graph(lat, lon, radius)
    nodes = list(G.nodes())

# Step 5: Custom Accessibility Cost Function
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

# Step 6: Route Calculation
if len(nodes) >= 2:
    orig_node = nodes[0]
    dest_node = nodes[-1]

    # Calculate Paths
    shortest_path = nx.shortest_path(G, orig_node, dest_node, weight='length')
    accessible_path = nx.shortest_path(G, orig_node, dest_node, weight=custom_cost)

    # Render Map using Folium
    m = folium.Map(location=[lat, lon], zoom_start=15)

    # Plot Shortest Path (Red)
    shortest_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in shortest_path]
    folium.PolyLine(shortest_coords, color="red", weight=5, opacity=0.8, tooltip="Standard Shortest Path").add_to(m)

    # Plot Accessible Path (Green)
    accessible_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in accessible_path]
    folium.PolyLine(accessible_coords, color="green", weight=5, opacity=0.8, tooltip="Accessible Path").add_to(m)

    # Display Map in Streamlit
    st_folium(m, width=900, height=500)
else:
    st.error("Not enough nodes found in this region. Try increasing the map radius.")