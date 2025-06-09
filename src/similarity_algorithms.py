import os
import sys
root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root)

import networkx as nx
from src.build_graph import load_graph, load_json_data
import json

# Ensure output directory exists
output_path = os.path.join(root,"dictionaries")
os.makedirs(output_path, exist_ok=True)

tasknames = [
        "startup_similarity",
        "startup_tech_similarity",
        "weighted_startup_similarity",
        "founder_similarity",
        "investor_similarity",
        "coinvestor_similarity",
        "weighted_investor_similarity"
        ]

# ------------------------------
# Task-based subgraph filtering
# ------------------------------

def subgraph_build(G,allowed_edge_types):
    filtered = nx.Graph()
    for u, v, data in G.edges(data=True):
        if data.get("type") in allowed_edge_types:
            filtered.add_node(u, **G.nodes[u])
            filtered.add_node(v, **G.nodes[v])
            filtered.add_edge(u, v, **data)
    return filtered

def get_startup_similarity_subgraph(G):
    allowed_edge_types = {"IN_INDUSTRY",
                          "IN_STAGE","HAS_BMODEL",
                          "HAS_TEAM_SIZE"}
    filtered = subgraph_build(G,allowed_edge_types)
    return filtered

def get_startup_tech_similarity_subgraph(G):
    allowed_edge_types = {"USES_TECH"}
    filtered = subgraph_build(G,allowed_edge_types)
    return filtered

def get_founder_similarity_subgraph(G):
    allowed_edge_types = {"HAS_EDU","HAS_EXP",
                          "HAS_EXPERTISE","HAS_BACKGROUND",
                          "IS_SERIAL_ENTREPRENEUR"}
    filtered = subgraph_build(G,allowed_edge_types)
    return filtered

def get_investor_similarity_subgraph(G):
    allowed_edge_types = {"HAS_THESIS","FOCUS_INDUSTRY","FOCUS_GEOGRAPHY"}
    filtered = subgraph_build(G,allowed_edge_types)
    return filtered

def get_coinvestor_similarity_subgraph(G):
    allowed_edge_types = {"INVESTED"}
    filtered = subgraph_build(G,allowed_edge_types)
    return filtered

# ------------------------------
# Run SimRank & save results
# ------------------------------

def compute_simrank_similarity(G, taskname, max_iterations=50, tolerance=1e-4):
    """
    Computes SimRank similarities for all nodes in the graph G and
    saves the results to a JSON file named "simrank_<taskname>.json".

    Parameters
    ----------
    G : networkx.Graph or networkx.DiGraph
        Input graph (undirected or directed).
    taskname : str
        Name of the task, used for naming the output file.
    max_iterations : int
        Max number of SimRank iterations.
    tolerance : float
        Convergence tolerance.
    """
    # 1. Compute full SimRank similarity matrix
    sim = nx.simrank_similarity(G, max_iterations=max_iterations, tolerance=tolerance)

    # 2. Convert to a standard dictionary and remove self-similarities
    sim_clean = {}
    for u in sim:
        sim_clean[u] = {
            v: round(score, 6)
            for v, score in sim[u].items()
            if u != v
        }

    # 3. Save to JSON file
    filename = os.path.join(output_path, f"simrank_{taskname}.json")
    with open(filename, "w") as f:
        json.dump(sim_clean, f, indent=2)

    print(f"SimRank similarities saved to '{filename}'")
    return sim_clean

def weighted_simrank_similarity(sim1, sim2, taskname, alpha=0.5):
    """
    Combine two SimRank similarity dictionaries using a weighted average.

    Parameters:
    - sim1: dict, similarity scores from the first SimRank run (e.g., using INVESTED edges).
    - sim2: dict, similarity scores from the second SimRank run (e.g., using HAS_THESIS edges).
    - taskname: str, name of the task to name the output file.
    - alpha: float, weight for sim1 (sim2 gets 1 - alpha).

    Returns:
    - sim_weighted: dict, weighted combined similarity scores.
    """
    sim_weighted = {}

    all_nodes = set(sim1.keys()).union(sim2.keys())

    for u in all_nodes:
        sim_weighted[u] = {}
        v_candidates = set(sim1.get(u, {}).keys()).union(sim2.get(u, {}).keys())

        for v in v_candidates:
            sim1_val = sim1.get(u, {}).get(v, 0.0)
            sim2_val = sim2.get(u, {}).get(v, 0.0)
            combined = alpha * sim1_val + (1 - alpha) * sim2_val
            sim_weighted[u][v] = round(combined, 6)

    # Save to JSON
    filename = os.path.join(output_path, f"simrank_{taskname}.json")
    with open(filename, "w") as f:
        json.dump(sim_weighted, f, indent=2)

    print(f"SimRank similarities saved to '{filename}'")
    return sim_weighted


# ------------------------------
# Query top-k similar nodes
# ------------------------------

def has_required_edges(G, node, required_edge_types):
    edges = G.edges(node, data="type")
    found_types = {edata for _, _, edata in edges}
    return all(t in found_types for t in required_edge_types)

def top_n_similar(G, sim, node_name, n=5, include_self=False):
    """
    Returns the top-n most similar nodes to the node with a given 'name' attribute,
    sorted by descending SimRank score.
    
    Parameters
    ----------
    G : networkx.Graph
        The knowledge graph.
    sim : dict[node, dict[node, float]]
        Output of nx.simrank_similarity(G).
    node_name : str
        The 'name' attribute of the node for which to find similar nodes.
    n : int
        Number of top similar nodes to return.
    include_self : bool
        Whether to include the node itself in the results.
    
    Returns
    -------
    List of (other_node, score), sorted by score descending.
    """
    # Find the node ID by matching 'name' attribute
    node_id = None
    for nid, attrs in G.nodes(data=True):
        if attrs.get("name") == node_name:
            node_id = nid
            break
    
    if node_id is None:
        raise ValueError(f"No node found with name attribute: {node_name}")
    
    # Get edge types connected to the node
    edges = G.edges(node_id, data="type")
    found_types = {edata for _, _, edata in edges}
    
    scores = sim.get(node_id, {})
    
    if not include_self:
        scores = {v: s for v, s in scores.items() if v != node_id}
    
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # Filter and map to names
    filtered = []
    for v, score in ranked:
        if has_required_edges(G, v, found_types):
            name = G.nodes[v].get("name")
            if name:
                filtered.append((name, score))
        if len(filtered) >= n:
            break

    # Fallback to top-n by score (even if not all match edge types)
    if not filtered:
        for v, score in ranked:
            name = G.nodes[v].get("name")
            if name:
                filtered.append((name, score))
            if len(filtered) >= n:
                break
    
    return filtered


# ------------------------------
# Get Similarity Dictionaries
# ------------------------------

tasks = {
    "startup_similarity": get_startup_similarity_subgraph,
    "startup_tech_similarity": get_startup_similarity_subgraph,
    "founder_similarity": get_founder_similarity_subgraph,
    "investor_similarity": get_investor_similarity_subgraph,
    "coinvestor_similarity": get_coinvestor_similarity_subgraph,
}

def get_similarity_dict(taskname):
    try:
        filename = os.path.join(output_path, f"simrank_{taskname}.json")
        similarity = load_json_data(filename)
    except:
        similarity = run_simrank_similarity_pipeline(taskname)
    return similarity

def get_similarity_dicts():
    similarities = {}
    for taskname in tasknames:
        similarities[taskname] = get_similarity_dict(taskname)
    return similarities

def run_simrank_similarity_pipeline(taskname):
    
    if taskname == "weighted_investor_similarity":
        investor_similarity = get_similarity_dict("investor_similarity")
        coinvestor_similarity = get_similarity_dict("coinvestor_similarity")
        similarity =weighted_simrank_similarity(investor_similarity,
                                                coinvestor_similarity,
                                                taskname,
                                                alpha=0.75) # 75% weight to investor similarity because it has 3 features out of 4
    
    elif taskname == "weighted_startup_similarity":
        startup_similarity = get_similarity_dict("startup_similarity")
        startup_tech_similarity = get_similarity_dict("startup_tech_similarity")
        similarity =weighted_simrank_similarity(startup_similarity,
                                                startup_tech_similarity,
                                                taskname,
                                                alpha=0.8) # 80% weight to startup similarity because it has 4 features out of 5
    else:
        G = load_graph()
        
        G_sub = tasks[taskname](G)
        similarity = compute_simrank_similarity(G_sub, taskname)

        # Test similarity query on a sample node
        example_node = None
        for node, attrs in G_sub.nodes(data=True):
            if "name" in attrs:
                example_node = node
                break

        if example_node is None:
            print("No node with a 'name' attribute was found.")
            return similarity

        example_name = G_sub.nodes[example_node]["name"]

        print(f"\nTop similar nodes to '{example_name}' in '{taskname}':")
        similar = top_n_similar(G_sub, similarity, example_name)

        for name, score in similar:
            print(f"{name}: {score:.3f}")
    
    return similarity



# ------------------------------
# Main
# ------------------------------

def main():
    get_similarity_dicts()

if __name__ == "__main__":
    main()
