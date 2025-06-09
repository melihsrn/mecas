import os
import sys
root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root)

import json
from collections import defaultdict, Counter
from itertools import combinations
from src.similarity_algorithms import get_similarity_dicts
from src.build_graph import load_json_data, load_graph

# Ensure output directory exists
output_path = os.path.join(root,"dictionaries")
os.makedirs(output_path, exist_ok=True)

similarities = get_similarity_dicts()

# ------------------------------
# Find co-investor pairs with co-invested startup counts
# ------------------------------

def find_coinvestors(G):
    # Dictionary to store co-invest counts
    coinvest_counts = defaultdict(lambda: defaultdict(int))

    # Loop over all startup nodes
    for node in G.nodes:
        if G.nodes[node].get("type") == "Startup":
            # Find all VCs that invested in this startup
            investors = [nbr for nbr in G.neighbors(node) if G.nodes[nbr].get("type") == "Venture_Capital"]
            
            # Count each VC pair as a co-investment
            for vc1, vc2 in combinations(sorted(investors), 2):
                coinvest_counts[vc1][vc2] += 1
                coinvest_counts[vc2][vc1] += 1  # undirected relationship

    # Convert defaultdict to regular dict for JSON serialization
    coinvest_counts_serializable = {
        vc1: dict(partners) for vc1, partners in coinvest_counts.items()
    }

    # Save to JSON file
    filename = os.path.join(output_path, "coinvestors.json")
    with open(filename, "w") as f:
        json.dump(coinvest_counts_serializable, f, indent=2)

    print(f"Saved co-investor data to '{filename}'")
    return coinvest_counts

def get_top_coinvestor_pairs(top_n=5):
    coinvestors = get_dict("coinvestors")
    pairs = []
    for vc1, partners in coinvestors.items():
        for vc2, count in partners.items():
            if vc1 < vc2:  # avoid duplicate pairs like (A, B) and (B, A)
                pairs.append(((vc1, vc2), count))
    
    top_pairs = sorted(pairs, key=lambda x: x[1], reverse=True)[:top_n]

    for (vc1, vc2), count in top_pairs:
        print(f"{vc1} and {vc2} co-invested in {count} startups")

    return top_pairs

def compute_total_funding(G):
    funding_amounts = defaultdict(float)

    for u, v, data in G.edges(data=True):
        if data.get("type") == "INVESTED":
            startup = v if G.nodes[v]["type"] == "Startup" else u
            amount = data.get("amount", 0.0)
            funding_amounts[startup] += amount / 1e6  # Convert to millions

    filename = os.path.join(output_path, "funding_amounts.json")
    # Convert defaultdict to dict and save
    with open(filename, "w") as f:
        json.dump(dict(funding_amounts), f, indent=2)
    
    print(f"Funding amounts saved to '{output_path}'")
    return dict(funding_amounts)


def get_popular_technologies(G, industry=None, top_n=10):

    tech_counter = Counter()

    for node in G.nodes:
        if G.nodes[node].get("type") != "Startup":
            continue

        # Industry filter
        if industry:
            has_industry = any(
                G.edges[node, neighbor]["type"] == "IN_INDUSTRY" and G.nodes[neighbor].get("type") == "Industry" and neighbor == industry
                for neighbor in G.neighbors(node)
            )
            if not has_industry:
                continue

        # Collect technologies used
        for neighbor in G.neighbors(node):
            if G[node][neighbor].get("type") == "USES_TECH" and G.nodes[neighbor].get("type") == "Technology":
                tech_counter[neighbor] += 1

    return tech_counter.most_common(top_n)

def count_startups_in_industry(G, industry_name):
    count = 0
    for u, v, data in G.edges(data=True):
        if data.get("type") == "IN_INDUSTRY":
            # Check if the edge connects a Startup to the desired industry
            if G.nodes[u].get("type") == "Startup" and v == industry_name:
                count += 1
            elif G.nodes[v].get("type") == "Startup" and u == industry_name:
                count += 1
    return count


def get_technologies_used_by_startup(G, startup_name):
    techs = []
    for u, v, data in G.edges(data=True):
        if data.get("type") == "USES_TECH":
            if G.nodes[u].get("type") == "Startup" and G.nodes[u].get("name") == startup_name:
                techs.append(G.nodes[v].get("name"))
            elif G.nodes[v].get("type") == "Startup" and G.nodes[v].get("name") == startup_name:
                techs.append(G.nodes[u].get("name"))
    return techs

def suggest_vcs_for_industry(G, industry_name, top_n=5):
    """
    Suggest VCs who have invested in startups in a given industry.

    Parameters
    ----------
    G : networkx.Graph
        The knowledge graph.
    industry_name : str
        The name of the target industry (e.g. "FinTech").
    top_n : int
        Number of VCs to return.

    Returns
    -------
    List of (vc_name, count_of_industry_investments)
    """
    # Find startup nodes in the given industry
    startups_in_industry = set()
    for u, v, data in G.edges(data=True):
        if data.get("type") == "IN_INDUSTRY":
            # Check if the edge connects a Startup to the desired industry
            if G.nodes[u].get("type") == "Startup" and v == industry_name:
                startups_in_industry.add(u)
            elif G.nodes[v].get("type") == "Startup" and u == industry_name:
                startups_in_industry.add(v)

    if not startups_in_industry:
        print(f"No startups found in industry: {industry_name}")
        return []

    # Count how many times each VC invested in those startups
    vc_counter = {}
    for startup, vc, data in G.edges(data=True):
        if data.get("type") == "INVESTED" and startup in startups_in_industry:
            if G.nodes[vc].get("type") == "Venture_Capital":
                vc_name = G.nodes[vc].get("name", vc)
                vc_counter[vc_name] = vc_counter.get(vc_name, 0) + 1

    ranked_vcs = sorted(vc_counter.items(), key=lambda x: x[1], reverse=True)
    return ranked_vcs[:top_n]


dicts = {
    "funding_amounts": compute_total_funding,
    "coinvestors": find_coinvestors,
}

def get_dict(name):
    try:
        filename = os.path.join(output_path, f"{name}.json")
        dict = load_json_data(filename)
    except:
        G = load_graph()
        dict = dicts[name](G)
    return dict

def get_dicts():
    dicts_ = {}
    for name in dicts.keys():
        dicts_[name] = get_dict(name)
    return dicts_

# ------------------------------
# Main
# ------------------------------

def main():
    get_dicts()

if __name__ == "__main__":
    main()