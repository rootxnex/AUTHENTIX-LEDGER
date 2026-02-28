"""Graph-based feature extraction using NetworkX for bot cluster detection."""
import pandas as pd
import numpy as np
import networkx as nx
from typing import Optional


def extract_graph_features(
    profiles_df: pd.DataFrame,
    edges_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute graph-level features for each profile.
    Features: degree centrality, in/out degree, PageRank,
    clustering coefficient, community isolatedness.
    """
    G = nx.DiGraph()
    G.add_nodes_from(profiles_df["profile_id"].tolist())
    for _, row in edges_df.iterrows():
        G.add_edge(row["source"], row["target"])

    # Undirected version for clustering coefficient
    G_undirected = G.to_undirected()

    print("  Computing PageRank...")
    pagerank = nx.pagerank(G, alpha=0.85, max_iter=100)

    print("  Computing clustering coefficients...")
    clustering = nx.clustering(G_undirected)

    print("  Computing degree centrality...")
    in_degree = dict(G.in_degree())
    out_degree = dict(G.out_degree())
    degree_centrality = nx.degree_centrality(G_undirected)

    # Community detection via connected components isolatedness
    # Nodes in very small components (size < 3) are suspicious
    components = list(nx.weakly_connected_components(G))
    component_size_map = {}
    for comp in components:
        for node in comp:
            component_size_map[node] = len(comp)

    records = []
    for pid in profiles_df["profile_id"]:
        pr = pagerank.get(pid, 0.0)
        cc = clustering.get(pid, 0.0)
        ind = in_degree.get(pid, 0)
        outd = out_degree.get(pid, 0)
        dc = degree_centrality.get(pid, 0.0)
        comp_size = component_size_map.get(pid, 1)

        io_ratio = outd / max(ind, 1)
        is_isolated = int(comp_size <= 2)
        is_hub = int(dc > 0.1)

        records.append({
            "profile_id": pid,
            "pagerank": round(pr, 6),
            "clustering_coeff": round(cc, 4),
            "in_degree": ind,
            "out_degree": outd,
            "io_degree_ratio": round(io_ratio, 4),
            "degree_centrality": round(dc, 6),
            "component_size": comp_size,
            "is_isolated_node": is_isolated,
            "is_hub_node": is_hub,
        })

    return pd.DataFrame(records).set_index("profile_id")
