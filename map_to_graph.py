import geopandas as gpd
import networkx as nx
import matplotlib.pyplot as plt
import os

# 1. Point to your shapefile (all accompanying files CPG, DBF, PRJ, SHX must be in the same folder)
#    You can choose London_Ward.shp or London_Ward_CityMerged.shp depending on which one you want.
shp_path = "C:\Coding\CBL-London-Crime-\London-wards-2018-ESRI"

# 2. Load into GeoPandas
gdf = gpd.read_file(shp_path)

# 3. Inspect your columns to find the ward code/name fields
print(gdf.columns)  
# e.g. you might see ['GSS_CODE','NAME','geometry'] or similar.

# 4. Re-project to a metric CRS for topology checks
gdf = gdf.to_crs(epsg=27700)  # British National Grid

# 5. Compute Queen contiguity via spatial index + touches()
sindex = gdf.sindex
adjacency = {}
for idx, geom in gdf.geometry.items():
    candidates = list(sindex.intersection(geom.bounds))
    neighbors = [
        i for i in candidates
        if i != idx and geom.touches(gdf.geometry[i])
    ]
    adjacency[idx] = neighbors


# 6. Build the NetworkX graph
G = nx.Graph()
for idx, row in gdf.iterrows():
    # replace 'GSS_CODE' and 'NAME' with whatever your attribute columns are called
    ward_code = row.get("GSS_CODE", row.get("WD21CD", None))
    ward_name = row.get("NAME", row.get("WD21NM", None))
    G.add_node(idx, code=ward_code, name=ward_name)

for idx, neighs in adjacency.items():
    for nbr in neighs:
        G.add_edge(idx, nbr)

# 7. Compute node positions from centroids
# Option A: use .items() on the GeoSeries
pos = {
    idx: (geom.centroid.x, geom.centroid.y)
    for idx, geom in gdf.geometry.items()
}



# 8. Plot the ward-adjacency graph
fig, ax = plt.subplots(figsize=(10, 10))
gdf.plot(ax=ax, color="lightgray", edgecolor="white", linewidth=0.5)
nx.draw_networkx_edges(G, pos, ax=ax, edge_color="red", alpha=0.3, width=0.5)
nx.draw_networkx_nodes(G, pos, ax=ax, node_size=10, node_color="blue")
ax.set_title("London Ward Queen-Contiguity Graph", fontsize=16)
ax.set_axis_off()
plt.tight_layout()
plt.show()


nx.write_gexf(G, "london_wards_graph.gexf")
