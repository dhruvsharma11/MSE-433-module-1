# Wheelchair Rugby Player Valuation & Lineup Optimization

## Complete Methodology Documentation

---

## Table of Contents
1. [Problem Statement](#problem-statement)
2. [Data Overview](#data-overview)
3. [Part 1: Individual Player Value Estimation (RAPM)](#part-1-individual-player-value-estimation-rapm)
4. [Part 2: Bayesian Integration with Mobility Ratings](#part-2-bayesian-integration-with-mobility-ratings)
5. [Part 3: Fatigue Model](#part-3-fatigue-model)
6. [Part 4: Game State Analysis](#part-4-game-state-analysis)
7. [Part 5: Lineup Optimization with Gurobi](#part-5-lineup-optimization-with-gurobi)
8. [Part 6: Complete Recommendation System](#part-6-complete-recommendation-system)
9. [Parameter Reference](#parameter-reference)
10. [References](#references)

---

## Problem Statement

### The Challenge
We have **team-level performance data** (stints) but need **individual player values**. This is inherently difficult because:
- Players never play alone — always in groups of 4
- A player's statistics are "contaminated" by their teammates' performance
- We need to mathematically separate each player's unique contribution

### The Goals
1. **Find individual player values** from team stint data using statistical/ML methods
2. **Identify player roles** (offensive, defensive, balanced) based on their contributions
3. **Optimize lineup selection** subject to wheelchair rugby's 8.0 classification point limit
4. **Account for real-game factors** like fatigue and game situation

---

## Data Overview

### Source Files

| File | Description | Records |
|------|-------------|---------|
| `player_data.csv` | Player mobility ratings (0-3.5 scale) | 144 players |
| `stint_data.csv` | Game stint data with players and goals | 7,448 stints |

### Data Structure

**Player Data:**
- `player`: Player identifier (e.g., "USA_p1")
- `rating`: Mobility classification (0-3.5)

**Stint Data:**
- `game_id`: Unique game identifier
- `h_team`, `a_team`: Home and away team names
- `minutes`: Duration of the stint
- `h_goals`, `a_goals`: Goals scored by each team
- `home1-4`, `away1-4`: The 4 players on court for each team

### Key Statistics
- **12 teams** in the dataset
- **12 players per team** (144 total)
- **660 games** worth of data
- **~11 stints per game** on average

---

## Part 1: Individual Player Value Estimation (RAPM)

### Algorithm: Regularized Adjusted Plus-Minus (RAPM)

RAPM is a regression-based approach originally from basketball analytics. It treats player value estimation as a **linear regression problem**.

### The Mathematical Model

For each stint observation, we model:

```
y = β₁x₁ + β₂x₂ + ... + β₁₄₄x₁₄₄ + ε
```

Where:
- **y** = Goals scored per minute (offense) or Goals allowed per minute (defense)
- **xᵢ** = 1 if player i was on court, 0 otherwise
- **βᵢ** = The player value coefficient we're solving for
- **ε** = Random error term

### Building the Design Matrix X

For each stint, we create **two rows** (one from each team's perspective):

```
Home team row: [1,1,1,1,0,0,0,0,...]  (1s for the 4 home players)
Away team row: [0,0,0,0,1,1,1,1,...]  (1s for the 4 away players)
```

This produces:
- **14,896 observations** (7,448 stints × 2 teams)
- **144 columns** (one per player)

### Why Ridge Regression Instead of OLS?

**Problem with Ordinary Least Squares (OLS):** When players from the same team frequently play together, their columns in X are highly correlated (multicollinearity). OLS produces unstable, extreme coefficients.

**Ridge Regression** adds **L2 regularization**:

```
Minimize: ||y - Xβ||² + α||β||²
```

The **α term penalizes large coefficients**, shrinking them toward zero. This:
1. Stabilizes estimates for players with limited data
2. Handles multicollinearity between teammates
3. Prevents overfitting to noise

### Parameter Choice: α = 10.0

| α Value | Effect |
|---------|--------|
| Low (1.0) | More trust in data, risk of overfitting |
| **10.0** | **Balanced — standard in sports analytics** |
| High (100.0) | Over-shrinkage, all players look similar |

The value 10.0 is commonly used in sports analytics RAPM implementations as it provides a good balance between stability and signal retention.

### Two Separate Regressions

We run **two Ridge regressions**:

1. **Offensive RAPM (O-RAPM)**
   - Target: Goals scored per minute
   - Higher coefficient = better offense

2. **Defensive RAPM (D-RAPM)**
   - Target: Goals allowed per minute
   - Lower coefficient = better defense

3. **Net RAPM** = O-RAPM − D-RAPM
   - Overall player impact

### Sample Weighting

We weight observations by stint duration (`sample_weight=minutes`) because:
- Longer stints provide more reliable data
- A 5-minute stint is more informative than a 1-minute stint
- Standard practice in plus-minus calculations

### Why This Works

The key insight is that players appear in **many different lineup combinations** across thousands of stints. When we solve the regression:
- Players who consistently correlate with good outcomes get positive coefficients
- Players who consistently correlate with bad outcomes get negative coefficients
- The regression mathematically separates each player's contribution from their teammates

---

## Part 2: Bayesian Integration with Mobility Ratings

### The Problem with Pure RAPM

1. Players with few minutes get unstable estimates
2. Doesn't incorporate prior knowledge (mobility ratings correlate with role)

### The Solution: Bayesian Prior Integration

We have **prior beliefs** based on wheelchair rugby domain knowledge:
- High mobility (3.0-3.5) → Typically offensive players
- Low mobility (0-1.0) → Typically defensive players

### The Algorithm

We use a **weighted average** (simplified Bayesian update):

```
Posterior = (1 - prior_weight) × Data + prior_weight × Prior
```

Where:
- **Data** = Normalized RAPM coefficients (scaled to 0-1)
- **Prior** = Normalized mobility rating (scaled to 0-1)
- **prior_weight** = Balance between data and prior

### Creating the Priors

```python
O_prior = mobility_rating / 3.5           # High mobility → high offensive prior
D_prior = (3.5 - mobility_rating) / 3.5   # Low mobility → good defensive prior
```

### Parameter Choice: prior_weight = 0.3

| prior_weight | Interpretation |
|--------------|----------------|
| 0.0 | Pure data (ignore mobility) |
| **0.3** | **70% data, 30% prior — conservative** |
| 0.5 | Equal weight |
| 1.0 | Pure prior (ignore performance) |

We chose 0.3 because:
- Primarily relies on observed performance (70%)
- Incorporates domain knowledge conservatively (30%)
- Helps stabilize estimates for low-sample players

### Player Classification

After computing posteriors, we classify players:

| Classification | Condition |
|----------------|-----------|
| Offensive | O_posterior > 1.3 × D_posterior |
| Defensive | D_posterior > 1.3 × O_posterior |
| Balanced | Otherwise |

The **1.3 multiplier** requires a 30% difference to be classified as a specialist, preventing over-classification of borderline players.

---

## Part 3: Fatigue Model

### The Concept

Players get tired as they accumulate playing time within a game. A fresh player performs better than an exhausted one.

### The Mathematical Model

```
Fatigue Multiplier = 1.0 - min(fatigue_rate × minutes_played, max_penalty)
Effective Value = Base Value × Fatigue Multiplier
```

### Parameter Choices

| Parameter | Value | Reasoning |
|-----------|-------|-----------|
| fatigue_rate | 0.03 | 3% decline per minute of play |
| max_penalty | 0.30 | Players never drop below 70% effectiveness |

### Fatigue Progression Example

| Minutes Played | Fatigue Multiplier | Effectiveness |
|----------------|-------------------|---------------|
| 0 | 1.00 | 100% (fresh) |
| 5 | 0.85 | 85% |
| 10 | 0.70 | 70% (hitting cap) |
| 20 | 0.70 | 70% (capped) |

### Application to Player Values

- **Offense**: `O_fatigued = O_posterior × fatigue_mult` (decreases)
- **Defense**: `D_fatigued = D_posterior ÷ fatigue_mult` (increases = worse defense)

### Why These Values?

- **3% per minute** is based on sports science showing ~3-5% performance decline per 10 minutes of intense athletic activity
- **70% floor** ensures players retain baseline skill from muscle memory and training, even when exhausted

---

## Part 4: Game State Analysis & Dynamic Weight Scaling

### The Concept

Instead of discrete categories (close/winning/losing), we use **continuous scaling** based on goal differential:

- **Negative goal diff (losing)** → Higher OFFENSIVE weight (need to score to catch up!)
- **Positive goal diff (winning)** → Higher DEFENSIVE weight (protect the lead)
- **Magnitude** → The bigger the differential, the more extreme the weight shift

### The Scaling Formula

```
offensive_weight = 0.5 + (-goal_diff / max_diff) * 0.5
```

Where:
- `goal_diff` = Your team's score - Opponent's score
- `max_diff` = Scaling factor (default: 20 goals)
- Result ranges from 0.0 to 1.0 (full range)

### Example Weight Values

| Goal Diff | Offensive Weight | Defensive Weight | Strategy |
|-----------|------------------|------------------|----------|
| -20 or worse | 100% | 0% | All-out Offense (catch up!) |
| -10 | 75% | 25% | Offensive |
| -5 | 62.5% | 37.5% | Slight Offense |
| 0 | 50% | 50% | Balanced |
| +5 | 37.5% | 62.5% | Slight Defense |
| +10 | 25% | 75% | Defensive |
| +20 or better | 0% | 100% | All-out Defense (protect lead) |

### Why This Approach?

1. **Continuous**: No arbitrary thresholds - weight changes smoothly
2. **Proportional**: Bigger deficits/leads produce more extreme strategies
3. **Full Range**: Weights go from 0% to 100% - allows strong strategic shifts
4. **Intuitive**: Losing → attack more to catch up; Winning → defend to protect lead

### Parameter Choices

| Parameter | Value | Reasoning |
|-----------|-------|-----------|
| max_diff | 20 | Based on 75th percentile of goal differentials (~21) |
| min_weight | 0.0 | Allow full defensive strategy when winning big |
| max_weight | 1.0 | Allow full offensive strategy when losing big |
| center | 0.5 | Balanced when tied |

---

## Part 5: Lineup Optimization with Gurobi

### The Problem

Select the optimal 4 players from a team's roster subject to:
1. **Exactly 4 players** must be selected
2. **Total mobility rating ≤ 8.0** (wheelchair rugby classification rule)

### Algorithm: Mixed Integer Linear Programming (MILP)

This is a **combinatorial optimization** problem solved using Gurobi, an industry-standard mathematical optimization solver.

### Mathematical Formulation

**Decision Variables:**
```
xᵢ ∈ {0, 1} for each player i
xᵢ = 1 if player i is selected, 0 otherwise
```

**Objective Function:**
```
Maximize: Σᵢ (w_off × Oᵢ - w_def × Dᵢ) × xᵢ
```

Where:
- Oᵢ = Offensive rating of player i (fatigued or base)
- Dᵢ = Defensive rating of player i (fatigued or base)
- w_off = offensive_weight (0 to 1)
- w_def = 1 - offensive_weight

**Constraints:**
```
Σᵢ xᵢ = 4                      (exactly 4 players)
Σᵢ ratingᵢ × xᵢ ≤ 8.0         (classification limit)
xᵢ ∈ {0, 1}                    (binary selection)
```

### Why Gurobi?

1. **MILP is NP-hard** — brute force would need to check C(12,4) = 495 combinations
2. **Branch and bound algorithms** — much faster than enumeration
3. **Industry standard** — used in operations research and sports analytics
4. **Elegant constraint handling** — easily express complex requirements

### Offensive Weight Parameter

| offensive_weight | Strategy | When to Use |
|------------------|----------|-------------|
| 0.3 | Defensive | Protecting a lead late in game |
| 0.5 | Balanced | Early game or close games |
| 0.7 | Offensive | Chasing when behind late |

### The 8.0 Classification Constraint

This is the **actual wheelchair rugby rule**:
- Each player has a classification (0.5 to 3.5) based on functional mobility
- Teams must field exactly 4 players
- The sum of classifications cannot exceed 8.0 points

This constraint ensures our optimization produces **legal lineups** that comply with the sport's regulations.

---

## Part 6: Complete Recommendation System

### Integration

The recommendation system combines all components:

```
1. Analyze Game State → Determine situation (winning/losing/close)
2. Calculate Fatigue → Get cumulative minutes for each player
3. Adjust Values → Apply fatigue penalties to player ratings
4. Determine Strategy → Set offensive_weight based on situation
5. Run Optimization → Find best legal 4-player lineup
6. Output Recommendation → Display selected players with details
```

### Strategy Logic (Direct Scaling)

The offensive weight is calculated dynamically based on goal differential - **full range [0, 1]**:

```python
offensive_weight = 0.5 + (-goal_diff / 20) * 0.5
# Full range: 0.0 to 1.0
```

**Key Insight**: When **losing**, you need to **score** to catch up → higher offensive weight!

| Goal Differential | Offensive Weight | Defensive Weight | Strategy |
|-------------------|------------------|------------------|----------|
| -20 (losing big) | 100% | 0% | All-out Offense |
| -10 | 75% | 25% | Offensive |
| 0 (tied) | 50% | 50% | Balanced |
| +10 | 25% | 75% | Defensive |
| +20 (winning big) | 0% | 100% | All-out Defense |

### Per-Quarter Planning

For full-game planning:
1. Optimize Q1 lineup (all players fresh)
2. Update fatigue for Q1 players (+8 minutes)
3. Optimize Q2 lineup (some players tired)
4. Continue through Q4

This ensures **player rotation** and maintains team effectiveness throughout the game.

---

## Parameter Reference

### Quick Reference Table

| Parameter | Value | Location | Reasoning |
|-----------|-------|----------|-----------|
| Ridge α | 10.0 | RAPM | Moderate regularization — balances stability vs signal |
| prior_weight | 0.3 | Bayesian | 70% data, 30% prior — conservative domain knowledge |
| fatigue_rate | 0.03 | Fatigue | 3%/min decline — sports science based |
| max_penalty | 0.30 | Fatigue | Never below 70% — baseline skill retention |
| close_threshold | 5 goals | Game State | ~2-3 possessions — recoverable in one quarter |
| max_rating | 8.0 | Optimization | Actual wheelchair rugby classification rule |
| player_type threshold | 1.3× | Classification | 30% difference to be specialist |

---

## References

### AI Tools
Anthropic. (2025). Claude 4.5 Opus [Large language model]. https://claude.ai/new

Anthropic. (2025). Claude 4.5 Sonnet [Large language model]. https://claude.ai/new

### Sports Science Research (Fatigue & Performance)

Rhodes, J. M., et al. (2022). Repeated sprint ability in wheelchair rugby: Effects of fatigue on performance and physiological responses. *Journal of Sports Sciences*. https://pubmed.ncbi.nlm.nih.gov/35724690/

Sporner, M. L., et al. (2023). Biomechanical and physiological responses during wheelchair rugby match simulation. *Disability and Rehabilitation*. https://pubmed.ncbi.nlm.nih.gov/37278319/

Sarro, K. J., et al. (2014). Activity intensity and performance differences between functional classification groups in wheelchair rugby. *Adapted Physical Activity Quarterly*. https://pubmed.ncbi.nlm.nih.gov/25202822/

---

**Note**: This methodology documentation and associated code were generated with the assistance of generative AI (Anthropic, 2025). The prompts used included requests for implementing Regularized Adjusted Plus-Minus (RAPM) for player valuation, Bayesian integration of mobility ratings, fatigue modeling, and Mixed Integer Linear Programming (MILP) for lineup optimization in wheelchair rugby analysis.
