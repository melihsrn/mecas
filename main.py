import re
from src.build_graph import load_graph
from src.similarity_algorithms import get_similarity_dict, top_n_similar
from src.graph_query_utils import (
    get_technologies_used_by_startup,
    count_startups_in_industry,
    suggest_vcs_for_industry
)

# ========== Extract Query Components ==========
def parse_query(query):
    query = query.strip()

    # Q1: Count startups by industry
    match = re.search(r"How many startups are in the ([\w&\s\-]+) industry\??", query)
    if match:
        industry = match.group(1).strip()
        return "count_startups", "industry", industry

    # Q2: Get technology stack of a startup
    match = re.search(r"What technologies does ([\w&\s\-]+) use\??", query)
    if match:
        startup_name = match.group(1).strip()
        return "startup_technologies", "startup", startup_name

    # Q3: Startups similar to a specific company
    match = re.search(r"Find \d+ startups most similar to ([\w&\s\-]+) in the AI/ML space", query)
    if match:
        company = match.group(1).strip()
        return "startup_similarity", "startup", company

    # Q4: Founders with similar backgrounds
    match = re.search(r"Find founders with similar backgrounds to ([\w&\s\-]+)\??", query)
    if match:
        founder_name = match.group(1).strip()
        return "founder_similarity", "founder", founder_name

    # Q5: VCs with similar investment patterns
    match = re.search(r"Which VCs have similar investment patterns to ([\w&\s\-]+)\??", query)
    if match:
        vc_name = match.group(1).strip()
        return "investor_similarity", "investor", vc_name

    # Q6: Companies with similar tech stacks
    match = re.search(r"Which companies have similar technology stacks to ([\w&\s\-]+)\??", query)
    if match:
        company = match.group(1).strip()
        return "startup_tech_similarity", "startup", company

    # Q7: VC Co-investment relationships
    match = re.search(r"Which VCs typically co-invest with ([\w&\s\-]+)\??", query)
    if match:
        vc_name = match.group(1).strip()
        return "coinvestor_similarity", "investor", vc_name

    # Q8: VCs to target based on industry
    match = re.search(r"If I'm a founder starting an ([\w&\s\-]+) company, which VCs should I target.*", query)
    if match:
        industry = match.group(1).strip()
        return "founder_target_vcs", "industry", industry

    return None, None, None

# ========= Format Response =========
def format_response(entity, type, results):
    if not results:
        return f"❌ No {type} similar to {entity} found."

    response = f"Here are {type} similar to **{entity}**:\n"
    for idx, (node, score) in enumerate(results, 1):
        response += f"{idx}. {node} (Similarity score: {score:.4f})\n"
    return response

# ========= Main =========
def main():
    query = input("Enter your query: ")
    taskname, type, entity = parse_query(query)

    if not taskname:
        print("❌ Sorry, I couldn't understand the query.")
        return

    G = load_graph()

    if taskname in [
        "startup_similarity",
        "founder_similarity",
        "investor_similarity",
        "startup_tech_similarity",
        "coinvestor_similarity"
    ]:
        print(f">>> Finding {type} similar to '{entity}'...\n")
        simrank_dict = get_similarity_dict(taskname)
        results = top_n_similar(G, simrank_dict, entity)
        response = format_response(entity, type, results)

    elif taskname == "founder_target_vcs":
        print(f">>> Suggesting VCs investing in successful '{entity}' startups...\n")
        results = suggest_vcs_for_industry(G, entity)
        if not results:
            response = f"No suitable VCs found for the {entity} industry."
        else:
            response = f"Suggested VCs for a {entity} startup:\n"
            for idx, (vc, score) in enumerate(results, 1):
                response += f"{idx}. {vc} (Score: {score:.3f})\n"

    elif taskname == "count_startups":
        print(f">>> Counting startups in the '{entity}' industry...\n")
        count = count_startups_in_industry(G, entity)
        response = f"There are {count} startups in the {entity} industry."

    elif taskname == "startup_technologies":
        print(f">>> Getting technologies used by {entity}...\n")
        techs = get_technologies_used_by_startup(G, entity)
        if not techs:
            response = f"No technologies found for {entity}."
        else:
            response = f"{entity} uses the following technologies:\n- " + "\n- ".join(techs)

    print("\n" + response)

if __name__ == "__main__":
    main()
