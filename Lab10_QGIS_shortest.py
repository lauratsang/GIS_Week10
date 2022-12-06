import osmnx as ox
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
place_name = "Kamppi, Helsinki, Finland"
graph = ox.graph_from_place(place_name, network_type='drive')
fig, ax = ox.plot_graph(graph)
edges = ox.graph_to_gdfs(graph, nodes=False, edges=True)
edges.columns
edges['highway'].value_counts()
print("Coordinate system:", edges.crs)
graph_proj = ox.project_graph(graph)
fig, ax = ox.plot_graph(graph_proj)
plt.tight_layout()
nodes_proj, edges_proj = ox.graph_to_gdfs(graph_proj, nodes=True, edges=True)
print("Coordinate system:", edges_proj.crs)
edges_proj.head()

stats = ox.basic_stats(graph_proj)
stats

area = edges_proj.unary_union.convex_hull.area
stats = ox.basic_stats(graph_proj, area=area)
extended_stats = ox.extended_stats(graph_proj, ecc=True, bc=True, cc=True)

for key, value in extended_stats.items():
    stats[key] = value

pd.Series(stats)
bbox = box(*edges_proj.unary_union.bounds)
print(bbox)

orig_point = bbox.centroid
print(orig_point)

nodes_proj['x'] = nodes_proj.x.astype(float)
maxx = nodes_proj['x'].max()

target_loc = nodes_proj.loc[nodes_proj['x']==maxx, :]
print(target_loc)

target_point = target_loc.geometry.values[0]
print(target_point)

orig_xy = (orig_point.y, orig_point.x)
target_xy = (target_point.y, target_point.x)
orig_node = ox.get_nearest_node(graph_proj, orig_xy, method='euclidean')
target_node = ox.get_nearest_node(graph_proj, target_xy, method='euclidean')

o_closest = nodes_proj.loc[orig_node]
t_closest = nodes_proj.loc[target_node]
print(orig_node)
print(target_node)
od_nodes = gpd.GeoDataFrame([o_closest, t_closest], geometry='geometry', crs=nodes_proj.crs)

route = nx.shortest_path(G=graph_proj, source=orig_node, target=target_node, weight='length')
print(route)

fig, ax = ox.plot_graph_route(graph_proj, route, origin_point=orig_xy, destination_point=target_xy)
plt.tight_layout()
    
    