"""
Wheelchair Rugby Lineup Optimizer

This module contains functions for:
- Calculating offensive/defensive weights based on game state
- Applying fatigue penalties to player values
- Optimizing lineups using Gurobi MILP
"""

import pandas as pd
import numpy as np
import gurobipy as gp
from gurobipy import GRB
from pathlib import Path


# Load pre-calculated player values
DATA_DIR = Path(__file__).parent / "data"


def load_player_values() -> pd.DataFrame:
    """Load pre-calculated player values from CSV."""
    return pd.read_csv(DATA_DIR / "player_values.csv")


def load_mobility_ratings() -> dict:
    """Load mobility ratings as a dictionary."""
    player_data = pd.read_csv(DATA_DIR / "player_data.csv")
    return dict(zip(player_data['player'], player_data['rating']))


def get_teams() -> list[str]:
    """Get list of all teams in the dataset."""
    player_values = load_player_values()
    return sorted(player_values['team'].unique().tolist())


def calculate_offensive_weight(goal_diff: int, max_diff: int = 20) -> float:
    """
    Calculate offensive weight based on goal differential.
    
    Simple direct scaling - full range [0, 1]:
    - Losing by 20+ → 100% offensive (need to score!)
    - Tied → 50/50 balanced
    - Winning by 20+ → 0% offensive (100% defensive, protect lead)
    
    Parameters:
    - goal_diff: Current goal differential (positive = winning)
    - max_diff: Goal differential that produces 0% or 100% weight (default 20)
    
    Returns:
    - offensive_weight: float between 0.0 and 1.0
    
    Examples:
    - goal_diff = -20 → offensive_weight = 1.00 (100% OFFENSE!)
    - goal_diff = -10 → offensive_weight = 0.75 (75% offense)
    - goal_diff = 0   → offensive_weight = 0.50 (balanced)
    - goal_diff = +10 → offensive_weight = 0.25 (25% offense)
    - goal_diff = +20 → offensive_weight = 0.00 (100% DEFENSE!)
    """
    # Normalize: flip sign so losing (negative) becomes positive
    normalized = -goal_diff / max_diff
    normalized = max(-1, min(1, normalized))  # Clamp to [-1, 1]
    
    # Scale to [0, 1]: 0.5 is center, shift by up to 0.5
    offensive_weight = 0.5 + (normalized * 0.5)
    
    return offensive_weight


def calculate_fatigue_penalty(minutes_played: float, fatigue_rate: float = 0.03, max_penalty: float = 0.30) -> float:
    """
    Calculate fatigue multiplier based on minutes played.
    
    Returns: float 0.7-1.0 (1.0 = fresh, 0.7 = max fatigue)
    """
    penalty = min(fatigue_rate * minutes_played, max_penalty)
    return 1.0 - penalty


def get_fatigue_adjusted_values(
    player_values: pd.DataFrame, 
    player_minutes: dict[str, float], 
    fatigue_rate: float = 0.03
) -> pd.DataFrame:
    """
    Adjust player values based on accumulated fatigue.
    
    Parameters:
    - player_values: DataFrame with player ratings
    - player_minutes: Dict mapping player -> minutes played
    - fatigue_rate: Rate of fatigue per minute (default 0.03)
    
    Returns:
    - DataFrame with fatigue-adjusted values
    """
    adjusted = player_values.copy()
    adjusted['minutes_played'] = adjusted['player'].map(lambda p: player_minutes.get(p, 0))
    adjusted['fatigue_mult'] = adjusted['minutes_played'].apply(
        lambda m: calculate_fatigue_penalty(m, fatigue_rate)
    )
    
    # Apply fatigue
    adjusted['O_fatigued'] = adjusted['O_posterior'] * adjusted['fatigue_mult']
    adjusted['D_fatigued'] = adjusted['D_posterior'] / adjusted['fatigue_mult']  # Defense gets worse
    adjusted['Net_fatigued'] = adjusted['O_fatigued'] - adjusted['D_fatigued']
    
    return adjusted


def optimize_lineup_gurobi(
    team_players: pd.DataFrame, 
    offensive_weight: float = 0.5, 
    max_rating: float = 8.0
) -> pd.DataFrame:
    """
    Find optimal 4-player lineup using Gurobi MILP.
    
    Parameters:
    - team_players: DataFrame with player values for one team
    - offensive_weight: 0-1, weight toward offense vs defense (0.5 = balanced)
    - max_rating: Maximum total mobility rating (default 8.0)
    
    Returns:
    - DataFrame with selected players
    """
    players = team_players['player'].tolist()
    n = len(players)
    
    # Get values (use fatigued if available, else posterior)
    if 'O_fatigued' in team_players.columns:
        o_vals = team_players['O_fatigued'].values
        d_vals = team_players['D_fatigued'].values
    else:
        o_vals = team_players['O_posterior'].values
        d_vals = team_players['D_posterior'].values
    
    ratings = team_players['mobility_rating'].values
    
    # Create Gurobi model
    m = gp.Model("LineupOptimization")
    m.setParam('OutputFlag', 0)  # Suppress solver output
    
    # Decision variables: x[i] = 1 if player i is selected
    x = m.addVars(n, vtype=GRB.BINARY, name="select")
    
    # Objective: Maximize weighted combination of offense - defense
    # Note: for defense, lower is better, so we subtract
    defensive_weight = 1 - offensive_weight
    m.setObjective(
        gp.quicksum(
            (offensive_weight * o_vals[i] - defensive_weight * d_vals[i]) * x[i] 
            for i in range(n)
        ),
        GRB.MAXIMIZE
    )
    
    # Constraint 1: Exactly 4 players
    m.addConstr(gp.quicksum(x[i] for i in range(n)) == 4, name="four_players")
    
    # Constraint 2: Total rating <= max_rating (8.0)
    m.addConstr(
        gp.quicksum(ratings[i] * x[i] for i in range(n)) <= max_rating, 
        name="rating_limit"
    )
    
    # Solve
    m.optimize()
    
    if m.status == GRB.OPTIMAL:
        selected_idx = [i for i in range(n) if x[i].X > 0.5]
        return team_players.iloc[selected_idx]
    else:
        raise ValueError(f"Optimization failed with status {m.status}")


def get_optimal_lineup(
    team: str,
    goal_diff: int,
    player_minutes: dict[str, float] | None = None,
    fatigue_rate: float = 0.03
) -> tuple[pd.DataFrame, float]:
    """
    Get optimal lineup for a team given current game state.
    
    Parameters:
    - team: Team name (e.g., 'Canada')
    - goal_diff: Current goal differential (positive = winning)
    - player_minutes: Dict mapping player -> minutes played this game
    - fatigue_rate: Rate of fatigue per minute
    
    Returns:
    - (selected_players DataFrame, offensive_weight)
    """
    # Load player values
    player_values = load_player_values()
    
    # Filter to team
    team_players = player_values[player_values['team'] == team].copy()
    
    # Apply fatigue if minutes provided
    if player_minutes:
        team_players = get_fatigue_adjusted_values(team_players, player_minutes, fatigue_rate)
    
    # Calculate weights based on goal differential
    offensive_weight = calculate_offensive_weight(goal_diff)
    
    # Optimize
    selected = optimize_lineup_gurobi(team_players, offensive_weight)
    
    return selected, offensive_weight


def get_strategy_label(offensive_weight: float) -> str:
    """Get human-readable strategy label from offensive weight."""
    if offensive_weight >= 0.7:
        return "HIGHLY OFFENSIVE"
    elif offensive_weight >= 0.55:
        return "OFFENSIVE"
    elif offensive_weight >= 0.45:
        return "BALANCED"
    elif offensive_weight >= 0.3:
        return "DEFENSIVE"
    else:
        return "HIGHLY DEFENSIVE"
