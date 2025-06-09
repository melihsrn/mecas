# 🚀 Mecas: Startup Knowledge Graph Framework Assignment

This is a Python-based framework for building and querying a knowledge graph of startups, founders, investors, technologies, and industries. It supports similarity analysis, complex investor relationships, and strategic business recommendations based on structured data.

---

## 📦 Features

- Build a knowledge graph of startups, founders, VCs, technologies, and industries.
- Support natural language queries for:
  - Similar startups, founders, or investors.
  - Co-investment patterns.
  - Strategic VC targeting by industry.
  - Technology stack and trend insights.
- Extensible to new tasks and query types.

---

## ⚙️ Setup Guide

### 1. Clone the repository

```bash
git clone https://github.com/melihsrn/mecas.git
cd mecas
```

### 2. Set up the Conda environment

```bash
conda create --name graph --file requirements.txt
conda activate graph
```

---

## 📁 Project Structure

```
mecas/
│
├── data/                        # Input CSV files (startup ecosystem datasets)
├── dictionaries/                # Output JSON files (similarity scores, cached answers)
├── graph/                       # Generated Knowledge Graph in .gpickle format
├── report/                      # Project overview and explanations
├── src/
│   ├── build_graph.py           # Build graph from CSVs
│   ├── similarity_algorithms.py# SimRank and other similarity logic
│   ├── graph_query_utils.py     # Utility functions for querying the graph
│   └── __init__.py              # Package initializer
│
├── main.py                      # CLI interface for querying
├── requirements.txt             # Required packages
└── README.md                    # You're here!
```

---

## 🔧 Data Requirements

Place the following preprocessed CSV files in the `data/` directory:

| File Name                                       | Description |
|------------------------------------------------|-------------|
| `startup_ecosystem_startups.csv`               | Startup metadata (with categorized employee counts) |
| `startup_ecosystem_founders.csv`               | Founder data (domain expertise & experience binned) |
| `startup_ecosystem_founder_startup.csv`        | Many-to-many founder-startup mapping |
| `startup_ecosystem_vcs.csv`                    | VC firm profiles (with exploded focus industries and investment stages) |
| `startup_ecosystem_investments.csv`            | Funding and investment records |
| `startup_ecosystem_technologies.csv`           | Technology definitions |
| `startup_ecosystem_startup_tech.csv`           | Technologies used per startup |

All preprocessing (e.g., exploding lists, binning years/employee count) is handled in `build_graph.py`.

---

## 🧠 How to Use

Run the CLI interface:

```bash
python main.py
```

You’ll be prompted to enter a natural language query. Supported examples include:

### 🟢 **Basic Functionality**
- `How many startups are in the FinTech industry?`
- `What technologies does OpenAI use?`

### 🧠 **Similarity-Based Insights**
- `Find 5 startups most similar to Hugging Face in the AI/ML space.`
- `Find founders with similar backgrounds to Elon Musk.`
- `Which VCs have similar investment patterns to Williams Ventures?`
- `Which companies have similar technology stacks to Stripe?`

### 🔗 **Complex Relationships**
- `Which VCs typically co-invest with Sequoia Capital?`

### 💼 **Business Applications**
- `If I'm a founder starting a HealthTech company, which VCs should I target based on similar successful investments?`

---

## 📊 Output

Results (e.g., similarity scores, matched entities, co-investor lists) are saved in `.json` files under the `dictionaries/` folder for caching and future access.

---

## 🧪 Extending the Framework

To support new types of questions:

1. Add query logic in `graph_query_utils.py` or `similarity_algorithms.py`.
2. Update the natural language parser in `main.py` to detect and route new patterns.

Example: Add a query type for “industry trend over time” → build subgraph filters by year.

---

## 👩‍💻 Development Notes

- Python 3.13
- Uses `networkx` for graph modeling and traversal.
- Run modules from the project **root directory** (`mecas/`) to avoid import path issues.
- Extensive use of `pandas`, `ast`, and custom query routing logic.

---

## 📫 Contact

**Email**: [melihsrnn@gmail.com](mailto:melihsrnn@gmail.com)  
**GitHub**: [github.com/melihsrn/mecas](https://github.com/melihsrn/mecas)

---

## 📝 License

MIT License. See [LICENSE](LICENSE) for details.
