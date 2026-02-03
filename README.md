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

**Step 1: Open the Notebook in Your IDE**

Open `analysis.ipynb` in VS Code, Cursor, or any IDE with Jupyter support.

**Step 2: Select Python Interpreter**

- Click on the kernel/interpreter selector (usually in top-right corner)
- Select the Python interpreter from your `venv` environment
- Should show: `venv (Python 3.x.x)`

**Step 3: Run All Cells**

Click **"Run All"** button at the top of the notebook, or run cells individually with `Shift + Enter`.

**What the notebook does:**
1. Loads stint and player data (`stint_data.csv`, `player_data.csv`)
2. Performs exploratory data analysis (EDA) - creates Tables A1, A2, A3
3. Calculates RAPM player values using Ridge regression
4. Applies Bayesian prior integration with mobility ratings
5. Generates all figures for the report:
   - Figure 1: Mobility vs RAPM correlation (r=0.688)
   - Figure 2: Prior weight sensitivity analysis
   - Fatigue model curve
   - Game state weighting visualization
   - Player type distribution scatter plot
6. Runs scenario analysis comparing observed vs model lineups (3 scenarios)
7. **Exports `player_values.csv`** (required for the web app)

**Expected runtime**: ~30 seconds to run all cells.

> **Note**: Make sure you've activated the virtual environment before opening your IDE so it can detect the correct Python interpreter.

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