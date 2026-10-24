import osmnx as ox

# Configure Custom User-Agent to avoid OSM blocking
ox.settings.user_agent = "AccessPath_Pedestrian_App_v1"
ox.settings.timeout = 60
ox.settings.log_console = True

print("Fetching pedestrian graph using direct coordinates (Chennai region)...")

try:
    # Direct Latitude and Longitude for IIT Madras / Adyar region (No address search needed)
    # Latitude: 12.9915, Longitude: 80.2337, Radius: 800 meters
    G = ox.graph_from_point((12.9915, 80.2337), dist=800, network_type="walk")

    print("\n-------------------------------------------")
    print("SUCCESS! Graph downloaded successfully.")
    print(f"Total Nodes (Intersections): {len(G.nodes)}")
    print(f"Total Edges (Pedestrian Paths): {len(G.edges)}")
    print("-------------------------------------------\n")

    # Inspect first edge accessibility attributes
    for u, v, k, data in list(G.edges(keys=True, data=True))[:2]:
        print(f"Path ({u} -> {v}):")
        print(f"  Highway type : {data.get('highway', 'N/A')}")
        print(f"  Length       : {round(data.get('length', 0), 2)} meters")
        print(f"  Wheelchair   : {data.get('wheelchair', 'Unknown / Missing')}")
        print(f"  Incline      : {data.get('incline', 'Unknown / Missing')}")
        print("-" * 35)

except Exception as e:
    print(f"\nError downloading graph: {e}")