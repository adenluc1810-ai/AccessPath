import osmnx as ox
import networkx as nx

# Enable local caching to prevent API timeout / rate limiting
ox.settings.use_cache = True
ox.settings.user_agent = "AccessPath_Pedestrian_App_v1"
ox.settings.timeout = 180

print("1. Downloading pedestrian graph for routing test...")

# Coordinates for IIT Madras, Chennai (500m bounding box for fast and reliable loading)
G = ox.graph_from_point((12.9915, 80.2337), dist=500, network_type="walk")

# Custom Accessibility & Uncertainty Cost Function
def custom_access_cost(u, v, data):
    # Retrieve edge data dictionary safely
    edge_data = data if isinstance(data, dict) else data[0] if isinstance(data, list) else {}
    
    length = edge_data.get('length', 1.0)
    highway = edge_data.get('highway', '')
    wheelchair = edge_data.get('wheelchair', 'unknown')
    incline = edge_data.get('incline', None)
    
    # Penalty Weights
    W_BARRIER = 200.0     # Severe penalty for stairs / non-wheelchair paths
    W_UNCERTAINTY = 20.0  # Moderate penalty for missing accessibility tags
    
    penalty = 0.0
    
    # 1. Physical Barrier Penalty
    if highway == 'steps' or wheelchair == 'no':
        penalty += W_BARRIER
        
    # 2. Uncertainty / Missing Tag Penalty
    if wheelchair == 'unknown' or incline is None:
        penalty += W_UNCERTAINTY
        
    return length + penalty

# Select Origin and Destination nodes
nodes = list(G.nodes())
origin_node = nodes[0]
destination_node = nodes[len(nodes) // 2]

print("2. Calculating Baseline Route (Standard Dijkstra Shortest Path)...")
baseline_path = nx.dijkstra_path(G, origin_node, destination_node, weight='length')
baseline_length = nx.dijkstra_path_length(G, origin_node, destination_node, weight='length')

print("3. Calculating AccessPath Route (Accessibility & Uncertainty Aware A*)...")
accesspath_route = nx.astar_path(G, origin_node, destination_node, weight=custom_access_cost)

# Calculate total physical length of AccessPath route
accesspath_length = 0.0
for i in range(len(accesspath_route) - 1):
    u = accesspath_route[i]
    v = accesspath_route[i+1]
    edge_info = G.get_edge_data(u, v)[0]
    accesspath_length += edge_info.get('length', 0.0)

# Calculate Detour Ratio
detour_ratio = accesspath_length / baseline_length if baseline_length > 0 else 1.0

print("\n================ ROUTE COMPARISON RESULTS ================")
print(f"Origin Node                : {origin_node}")
print(f"Destination Node           : {destination_node}")
print(f"Baseline Distance          : {round(baseline_length, 2)} meters")
print(f"AccessPath Distance        : {round(accesspath_length, 2)} meters")
print(f"Detour Ratio               : {round(detour_ratio, 3)} x")
print(f"Baseline Path Node Count   : {len(baseline_path)}")
print(f"AccessPath Path Node Count : {len(accesspath_route)}")
print("==========================================================\n")