# Wheelchair Rugby Lineup Optimizer

A data-driven lineup optimization system for wheelchair rugby.

**Course**: MSE 433 - Operations Research

---

## Project Structure

```
WCR/
├── analysis.ipynb      # Main analysis notebook (run this to reproduce all results)
├── app.py              # Streamlit web application
├── optimizer.py        # Core optimization functions used by app.py
├── requirements.txt    # Python dependencies
└── data/
    ├── stint_data.csv      # Raw game data (7,448 stints)
    ├── player_data.csv     # Player mobility ratings (144 players)
    └── player_values.csv   # Generated player values (created by notebook)
```

---

## Setup

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up Gurobi license (free for academics)
# Get license at: https://www.gurobi.com/academia/academic-program-and-licenses/
grbgetkey YOUR-LICENSE-KEY
```

---

## Usage

### Reproduce All Results
```bash
jupyter notebook analysis.ipynb
```
Run all cells in order. This generates all figures, tables, and exports `player_values.csv`.

### Run Web App
```bash
streamlit run app.py
```
Open http://localhost:8501 in your browser.

**What the app does**: Simulates a wheelchair rugby game where coaches can track stints and get real-time lineup recommendations.

1. Select two teams to start a game
2. Record each stint by selecting 4 players and entering goals scored
3. Click "Get Optimal Lineup" to receive model recommendations based on:
   - Current score differential (adjusts offensive/defensive strategy)
   - Player fatigue (accumulated minutes played)
   - 8.0 mobility constraint (ensures legal lineups)

---

## References

- Rhodes et al. (2022). Repeated sprint ability in wheelchair rugby. [PubMed](https://pubmed.ncbi.nlm.nih.gov/35724690/)