import streamlit as st
import osmnx as ox
import networkx as nx
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# Streamlit Page Config
st.set_page_config(page_title="AccessPath - Google Maps View", layout="wide")

st.title("♿ AccessPath: Uncertainty-Aware Pedestrian Route Planner")
st.write("Comparing **Standard Shortest Path (Red)** vs **Accessibility-Weighted Path (Green)**.")

# OSMnx Settings
ox.settings.user_agent = "AccessPathPedestrianApp/1.0"
ox.settings.timeout = 180
ox.settings.use_cache = True

@st.cache_data(show_spinner=False)
def get_lat_lon(place_name):
    try:
        geolocator = Nominatim(user_agent="AccessPathPedestrianApp/1.0")
        location = geolocator.geocode(place_name)
        if location:
            return location.latitude, location.longitude
    except Exception:
        pass
    return None, None

def get_nearest_node(G, lat, lon):
    best_node = None
    min_dist = float('inf')
    for n, data in G.nodes(data=True):
        n_lat = data.get('y')
        n_lon = data.get('x')
        if n_lat is not None and n_lon is not None:
            d = (n_lat - lat)**2 + (n_lon - lon)**2
            if d < min_dist:
                min_dist = d
                best_node = n
    return best_node

@st.cache_data(show_spinner=False, ttl=3600)
def load_map_graph(lat, lon, radius):
    return ox.graph_from_point((lat, lon), dist=radius, network_type="walk", truncate_by_edge=False)

# Sidebar Configuration - Search Place Names
st.sidebar.header("📍 Route Search")
start_place = st.sidebar.text_input("Start Location Name", value="Chennai Central, Chennai")
dest_place = st.sidebar.text_input("Destination Name", value="Ripon Building, Chennai")

radius = st.sidebar.slider("Map Radius (meters)", min_value=300, max_value=1200, value=600, step=100)

st.sidebar.header("⚙️ Accessibility Weights")
w_barrier = st.sidebar.slider("Barrier Penalty Weight (Stairs/Curb)", 50, 500, 200)
w_uncertainty = st.sidebar.slider("Uncertainty Penalty Weight (Missing Tags)", 0, 100, 20)

# Resolve Start and Destination Coordinates
start_lat, start_lon = get_lat_lon(start_place)
dest_lat, dest_lon = get_lat_lon(dest_place)

if not start_lat or not start_lon:
    start_lat, start_lon = 13.0827, 80.2707
if not dest_lat or not dest_lon:
    dest_lat, dest_lon = 13.0839, 80.2725

center_lat = (start_lat + dest_lat) / 2
center_lon = (start_lon + dest_lon) / 2

with st.spinner("⚡ Fetching Street Network..."):
    try:
        G = load_map_graph(center_lat, center_lon, radius)
    except Exception as e:
        st.error("Street network load aagala. Radius-a increase panni try pannunga.")
        st.stop()

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

orig_node = get_nearest_node(G, start_lat, start_lon)
dest_node = get_nearest_node(G, dest_lat, dest_lon)

if orig_node and dest_node and orig_node != dest_node:
    shortest_path = nx.shortest_path(G, orig_node, dest_node, weight='length')
    accessible_path = nx.shortest_path(G, orig_node, dest_node, weight=custom_cost)

    shortest_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in shortest_path]
    accessible_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in accessible_path]

    orig_pos = (G.nodes[orig_node]['y'], G.nodes[orig_node]['x'])
    dest_pos = (G.nodes[dest_node]['y'], G.nodes[dest_node]['x'])

    # EXACT GOOGLE MAPS TILE LAYER
    m = folium.Map(location=[center_lat, center_lon], zoom_start=16, tiles=None)

    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
        attr='Google Maps',
        name='Google Maps',
        overlay=False,
        control=True
    ).add_to(m)

    # Start and Destination Markers
    folium.Marker(
        orig_pos, 
        popup=f"📍 <b>Start:</b> {start_place}", 
        tooltip="Start Location",
        icon=folium.Icon(color="blue", icon="play")
    ).add_to(m)
    
    folium.Marker(
        dest_pos, 
        popup=f"🏁 <b>Destination:</b> {dest_place}", 
        tooltip="Destination Location",
        icon=folium.Icon(color="red", icon="flag")
    ).add_to(m)

    # Plot Routes (Google style thick line)
    folium.PolyLine(shortest_coords, color="#EA4335", weight=7, opacity=0.8, tooltip="Standard Shortest Path (Red)").add_to(m)
    folium.PolyLine(accessible_coords, color="#1A73E8", weight=7, opacity=0.9, tooltip="Accessible Path (Blue)").add_to(m)

    all_coords = shortest_coords + accessible_coords
    m.fit_bounds(all_coords)

    st_folium(m, width="100%", height=550)
else:
    st.warning("Start & Destination points-ukku route kandupidikka mudiyala. Map Radius slider-a increase pannunga.")