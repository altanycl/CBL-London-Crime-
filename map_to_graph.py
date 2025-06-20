import geopandas as gpd
import networkx as nx
import matplotlib.pyplot as plt

# 1. Load your LSOA file (still in WGS84, so LAT/LONG are valid)
shp_path = r"C:\Coding\CBL-London-Crime-\LSOA_boundries\LSOA_2021_EW_BFE_V10.shp"
gdf = gpd.read_file(shp_path)

# 2. Filter by the approx. London bounding box in degrees
#    West  = -0.5103, East  = +0.3340
#    South = 51.2868,  North = 51.6919
london = gdf[
    (gdf["LONG"] >= -0.5103) &
    (gdf["LONG"] <=  0.3340) &
    (gdf["LAT"]  >= 51.2868) &
    (gdf["LAT"]  <= 51.6919)
].copy()
london = london.reset_index(drop=True)

print(f"Kept {len(london)} LSOAs in the London box (out of {len(gdf)})")

# 3) Re-project
london = london.to_crs(epsg=27700)

# 4) Spatial index & adjacency
sindex = london.sindex
adjacency = {}
for idx, geom in london.geometry.items():       # idx == 0…n-1 now
    candidates = list(sindex.intersection(geom.bounds))
    adjacency[idx] = [
        j for j in candidates
        if j != idx
           and geom.touches(london.geometry.iloc[j])  # use iloc to be safe
    ]


# 5. Build the graph
G = nx.Graph()
for idx, row in london.iterrows():
    G.add_node(idx, lsoa_code=row["LSOA21CD"])
for idx, neighs in adjacency.items():
    for nbr in neighs:
        G.add_edge(idx, nbr)

# 6. (Optional) Plot for sanity check
pos = {i: geom.centroid.coords[0] for i, geom in london.geometry.items()}
fig, ax = plt.subplots(1,1,figsize=(6,6))
london.plot(ax=ax, color="lightgray", edgecolor="white")
nx.draw_networkx_edges(G, pos, ax=ax, edge_color="red", alpha=0.3, width=0.5)
nx.draw_networkx_nodes(G, pos, ax=ax, node_size=5, node_color="blue")
ax.set_axis_off()
plt.show()

# 7. Save
nx.write_gexf(G, "london_lsoa_graph.gexf")
print("Graph saved.")
