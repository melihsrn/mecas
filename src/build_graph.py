import os
import sys
root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root)

import networkx as nx
import pandas as pd
import json
import pickle
import ast

def load_csv_data(filepath):
    return pd.read_csv(filepath)
    
def load_json_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

data_path = os.path.join(root,"data")

# Ensure output directory exists
output_path = os.path.join(root,"graph")
os.makedirs(output_path, exist_ok=True)
filename = os.path.join(output_path, "knowledge_graph.gpickle")

# Load and preprocess data here
founder_startup = load_csv_data(data_path + "/startup_ecosystem_founder_startup.csv")


founders = load_csv_data(data_path + "/startup_ecosystem_founders.csv")
founders["domain_expertise"] = founders["domain_expertise"].apply(ast.literal_eval)
founders = founders.explode('domain_expertise').reset_index(drop=True)
founders["years_experience_categorized"] = None
founders.loc[(founders["years_experience"]<7),"years_experience_categorized"] = "0-6 years"
founders.loc[(founders["years_experience"]>=7) & (founders["years_experience"]<13),"years_experience_categorized"] = "7-12 years"
founders.loc[(founders["years_experience"]>=13) & (founders["years_experience"]<19),"years_experience_categorized"] = "13-18 years"
founders.loc[(founders["years_experience"]>=19), "years_experience_categorized"] = "19+ years"


investments = load_csv_data(data_path + "/startup_ecosystem_investments.csv")


startups = load_csv_data(data_path + "/startup_ecosystem_startups.csv")
startups["employee_count_categorized"] = None
startups.loc[(startups["employee_count"]<100),"employee_count_categorized"]= "0-99 employees"
startups.loc[(startups["employee_count"]>=100) & (startups["employee_count"]<200),"employee_count_categorized"] = "100-199 employees"
startups.loc[(startups["employee_count"]>=200) & (startups["employee_count"]<300),"employee_count_categorized"] = "200-299 employees"
startups.loc[(startups["employee_count"]>=300) & (startups["employee_count"]<400),"employee_count_categorized"] = "300-399 employees"
startups.loc[(startups["employee_count"]>=400),"employee_count_categorized"] = "400+ employees"


technologies = load_csv_data(data_path + "/startup_ecosystem_technologies.csv")


technology_used = load_csv_data(data_path + "/startup_ecosystem_startup_tech.csv")


vcs = load_csv_data(data_path + "/startup_ecosystem_vcs.csv")
vcs["focus_industries"] = vcs["focus_industries"].apply(ast.literal_eval)
vcs = vcs.explode('focus_industries').reset_index(drop=True)
vcs["investment_stage"] = ["When " + stage for stage in vcs["investment_stage"].to_list()]


def create_knowledge_graph():
    G = nx.Graph()

    # Add Company nodes
    for data in startups.to_numpy():
        attrs = {"name": data[1],
                 "description": data[2],
                 "location": data[4],
                 "founded_date": data[5],
                 "employee_count": data[7],
                 "website": data[8],
                 "revenue_model": data[10],
                 "status": data[11],
                  }
        G.add_node(data[0],**attrs, type="Startup")
        G.add_node(data[6], type="Stage")
        G.add_node(data[9], type="Business_Model")
        G.add_node(data[12], type="Team_Size")
        
        G.add_edge(data[0], data[3], type="IN_INDUSTRY")
        G.add_edge(data[0], data[6], type="IN_STAGE")
        G.add_edge(data[0], data[9], type="HAS_BMODEL")
        G.add_edge(data[0], data[12], type="HAS_TEAM_SIZE")
        
    for data in founders.to_numpy():
        attrs = {"name": data[1],
                 "email": data[2],
                 "linkedin_url": data[3],
                 "location": data[4],
                 "founded_date": data[5],
                 "years_experience": data[6],
                  "previous_company": data[7],
                  "created_at": data[11],
                  }
        G.add_node(data[0], **attrs, type="Founder")
        G.add_node(data[5], type="Education")
        G.add_node(data[8], type="Domain")
        G.add_node(data[9], type="Background")
        G.add_node(data[10], type="Serial_Entrepreneur")
        G.add_node(data[12], type="Experience")
        
        G.add_edge(data[0], data[5], type="HAS_EDU")
        G.add_edge(data[0], data[8], type="HAS_EXPERTISE")
        G.add_edge(data[0], data[9], type="HAS_BACKGROUND")
        G.add_edge(data[0], data[10], type="IS_SERIAL_ENTREPRENEUR")
        G.add_edge(data[0], data[12], type="HAS_EXP")
        
    for data in founder_startup.to_numpy():
        attrs = {"role":data[2],"equity_percentage":data[3], "is_active": data[4]}
        G.add_edge(data[0], data[1],**attrs, type="FOUNDED")
    
    for data in vcs.to_numpy():
        attrs = {"name": data[1],
                "location": data[2],
                "founded_year": data[3],
                "aum": data[4],
                "check_size_min": data[8],
                "check_size_max": data[9],
                "portfolio_size": data[10],
                }
        G.add_node(data[0],**attrs, type="Venture_Capital")
        G.add_node(data[5], type="Investment_Thesis")
        G.add_node(data[7], type="Geography")
        
        G.add_edge(data[0], data[5], type="HAS_THESIS")
        G.add_edge(data[0], data[6], type="FOCUS_INDUSTRY")
        G.add_edge(data[0], data[7], type="FOCUS_GEOGRAPHY")
        
    for data in investments.to_numpy():
        attrs = {"round_type":data[3],"amount":data[4],
                 "date": data[5], "is_lead_investor": data[7],
                 "valuation": data[6]}
        G.add_edge(data[2], data[1],**attrs, type="INVESTED")
    
    for data in technologies.to_numpy():
        attrs = {"name": data[1],
                 "category": data[2],
                 "popularity_score": data[3],
                 "maturity": data[4]
                  }
        G.add_node(data[0],**attrs, type="Technology")
        
    for data in technology_used.to_numpy():
        attrs = {"usage_intensity": data[2],
                 "implementation_date": data[3]
                  }
        G.add_edge(data[0], data[1],**attrs, type="USES_TECH")

    return G



def save_graph(G, filename=filename):
    with open(filename, 'wb') as f:
        pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)

def load_graph(filename=filename):
    try:
        with open(filename, 'rb') as f:
            G = pickle.load(f)
    except:
        G = create_knowledge_graph()
        save_graph(G,filename)
    return G

def main():
    # Create and save the graph
    G = create_knowledge_graph()
    save_graph(G,filename)

if __name__ == "__main__":
    main()
