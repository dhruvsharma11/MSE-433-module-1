"""
Wheelchair Rugby Lineup Optimizer - Streamlit App

A clean, modern single-page interface for:
1. Recording stint data (prior data input)
2. Getting optimal lineup recommendations
"""

import streamlit as st
import pandas as pd

from optimizer import (
    get_teams,
    get_optimal_lineup,
    load_player_values,
    calculate_offensive_weight,
    calculate_fatigue_penalty,
)


# Page configuration
st.set_page_config(
    page_title="WCR Lineup Optimizer",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# Modern CSS styling to match React component
st.markdown("""
<style>
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container */
    .main .block-container {
        padding: 0;
        max-width: 100%;
    }
    
    /* Score header */
    .score-header {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 1.5rem 2rem;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 3rem;
        margin-bottom: 2rem;
    }
    
    .team-score {
        text-align: center;
        color: white;
    }
    
    .team-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        opacity: 0.7;
        margin-bottom: 0.25rem;
    }
    
    .score-value {
        font-size: 3rem;
        font-weight: 700;
        line-height: 1;
    }
    
    .team-name {
        font-size: 0.9rem;
        margin-top: 0.25rem;
        opacity: 0.9;
    }
    
    .diff-display {
        text-align: center;
        color: white;
    }
    
    .diff-label {
        font-size: 0.65rem;
        text-transform: uppercase;
        opacity: 0.5;
    }
    
    .diff-value {
        font-size: 1.25rem;
        opacity: 0.7;
    }
    
    /* Section header */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .section-indicator {
        width: 4px;
        height: 24px;
        border-radius: 2px;
    }
    
    .indicator-yellow {
        background-color: #eab308;
    }
    
    .indicator-rose {
        background-color: #f43f5e;
    }
    
    .section-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: #111827;
    }
    
    /* Card styling */
    .card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .card-header {
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #e5e7eb;
        font-weight: 500;
        color: #111827;
    }
    
    .card-body {
        padding: 1rem;
    }
    
    /* Strategy badge */
    .strategy-container {
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        border-radius: 0.5rem;
        padding: 0.75rem 1rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .strategy-badge {
        display: inline-block;
        background: #10b981;
        color: white;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        margin-bottom: 0.5rem;
    }
    
    .strategy-weights {
        font-size: 0.75rem;
        color: #4b5563;
    }
    
    /* Player card */
    .player-card {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem;
        background: #f9fafb;
        border: 1px solid #f3f4f6;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .player-number {
        width: 2rem;
        height: 2rem;
        background: #2563eb;
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.875rem;
    }
    
    .player-info {
        flex: 1;
    }
    
    .player-name {
        font-weight: 500;
        color: #111827;
    }
    
    .player-stats {
        font-size: 0.75rem;
        color: #6b7280;
        margin-top: 0.125rem;
    }
    
    /* Stats row */
    .stats-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        padding: 0.75rem 1rem;
        background: #f9fafb;
        border-top: 1px solid #e5e7eb;
        text-align: center;
    }
    
    .stat-label {
        font-size: 0.75rem;
        color: #6b7280;
        margin-bottom: 0.125rem;
    }
    
    .stat-value {
        font-weight: 600;
        color: #111827;
    }
    
    .stat-value.blue {
        color: #2563eb;
    }
    
    .stat-value.green {
        color: #10b981;
    }
    
    /* Metrics */
    .metrics-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .metric-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        padding: 1rem;
    }
    
    .metric-label {
        font-size: 0.75rem;
        color: #6b7280;
        margin-bottom: 0.25rem;
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 600;
        color: #111827;
    }
    
    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 2rem;
        color: #9ca3af;
    }
    
    /* Button override */
    .stButton > button {
        border-radius: 0.5rem;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 500;
    }
    
    /* Content area padding */
    .content-area {
        padding: 0 2rem 2rem 2rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'home_team': None,
        'away_team': None,
        'stints': [],
        'player_minutes': {},
        'game_started': False,
        'optimal_result': None,
        'selected_players': [],  # Persist selected players across reruns
        'stint_just_added': False,  # Flag to reset goals/duration
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_team_players(team: str) -> pd.DataFrame:
    """Get all players for a team with their ratings."""
    player_values = load_player_values()
    return player_values[player_values['team'] == team].copy()


def format_player_name(player: str) -> str:
    """Format player name for display (e.g., Canada_p1 -> Canada 1)."""
    # Handle Great Britain special case
    if 'Great Britain' in player or 'Great_Britain' in player:
        parts = player.replace('Great Britain', 'Great_Britain').split('_')
        if len(parts) >= 2:
            num = parts[-1].replace('p', '')
            return f"Great_Britain_{num}"
    
    # Standard format: Team_pN -> Team_N
    parts = player.split('_')
    if len(parts) >= 2:
        team = parts[0]
        num = parts[-1].replace('p', '')
        return f"{team}_{num}"
    return player


def get_total_score() -> tuple[int, int]:
    """Calculate total score from all stints."""
    home = sum(s['home_goals'] for s in st.session_state.stints)
    away = sum(s['away_goals'] for s in st.session_state.stints)
    return home, away


def get_goal_diff() -> int:
    """Get current goal differential."""
    home, away = get_total_score()
    return home - away


def add_stint(lineup: list, home_goals: int, away_goals: int, duration: float):
    """Add a new stint to the history."""
    stint = {
        'stint_num': len(st.session_state.stints) + 1,
        'lineup': lineup,
        'home_goals': home_goals,
        'away_goals': away_goals,
        'duration': duration,
    }
    st.session_state.stints.append(stint)
    
    # Update player minutes
    for player in lineup:
        st.session_state.player_minutes[player] = (
            st.session_state.player_minutes.get(player, 0) + duration
        )


def reset_game():
    """Reset all game state."""
    st.session_state.stints = []
    st.session_state.player_minutes = {}
    st.session_state.game_started = False
    st.session_state.optimal_result = None
    st.session_state.selected_players = []


def render_score_header(home_team: str, away_team: str, home_score: int, away_score: int):
    """Render the score header."""
    goal_diff = home_score - away_score
    diff_text = str(goal_diff) if goal_diff <= 0 else f"+{goal_diff}"
    
    st.markdown(f"""
    <div class="score-header">
        <div class="team-score">
            <div class="team-label">HOME</div>
            <div class="score-value">{home_score}</div>
            <div class="team-name">{home_team}</div>
        </div>
        <div class="diff-display">
            <div class="diff-label">DIFF</div>
            <div class="diff-value">{diff_text}</div>
        </div>
        <div class="team-score">
            <div class="team-label">AWAY</div>
            <div class="score-value">{away_score}</div>
            <div class="team-name">{away_team}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    init_session_state()
    
    teams = get_teams()
    
    # Team selection screen
    if not st.session_state.game_started:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🏀 Wheelchair Rugby Lineup Optimizer")
        st.markdown("Select teams to begin")
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            home_team = st.selectbox("Home Team", teams, index=teams.index('Canada') if 'Canada' in teams else 0)
        
        with col2:
            st.markdown("<div style='text-align: center; padding-top: 28px; font-size: 1.5rem; color: #888;'>vs</div>", unsafe_allow_html=True)
        
        with col3:
            away_team = st.selectbox("Away Team", [t for t in teams if t != home_team])
        
        st.session_state.home_team = home_team
        st.session_state.away_team = away_team
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Start Game", type="primary", use_container_width=True):
            st.session_state.game_started = True
            st.rerun()
        
        return
    
    # Main game interface
    home_team = st.session_state.home_team
    away_team = st.session_state.away_team
    home_score, away_score = get_total_score()
    goal_diff = get_goal_diff()
    
    # Score header
    render_score_header(home_team, away_team, home_score, away_score)
    
    # Content area
    st.markdown('<div class="content-area">', unsafe_allow_html=True)
    
    # Two-column layout
    col_left, col_right = st.columns([1, 1], gap="large")
    
    # LEFT: Prior Stint Data
    with col_left:
        st.markdown("""
        <div class="section-header">
            <div class="section-indicator indicator-yellow"></div>
            <div class="section-title">Prior Stint Data</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add New Stint
        with st.expander("➕ Add New Stint", expanded=len(st.session_state.stints) == 0):
            team_players = get_team_players(home_team)
            
            # Get current selection from session state
            current_selection = st.session_state.selected_players
            
            # Calculate current mobility of selected players
            current_mobility = sum(
                team_players[team_players['player'] == p]['mobility_rating'].values[0]
                for p in current_selection
                if p in team_players['player'].values
            )
            
            # Filter available players: only show those that fit within remaining mobility budget
            remaining_budget = 8.0 - current_mobility
            
            # Build list of available players (already selected + those that fit)
            available_players = []
            for _, row in team_players.iterrows():
                player = row['player']
                mobility = row['mobility_rating']
                # Include if already selected OR if they fit in remaining budget
                if player in current_selection or mobility <= remaining_budget:
                    available_players.append(player)
            
            selected_players = st.multiselect(
                "Select 4 players",
                available_players,
                default=[p for p in current_selection if p in available_players],
                max_selections=4,
                format_func=format_player_name,
                key="player_select"
            )
            
            # Update session state with current selection
            st.session_state.selected_players = selected_players
            
            if selected_players:
                total_mobility = sum(
                    team_players[team_players['player'] == p]['mobility_rating'].values[0]
                    for p in selected_players
                )
                mobility_color = "#10b981" if total_mobility <= 8.0 else "#ef4444"
                st.markdown(f"Total Classification: <span style='color: {mobility_color}; font-weight: 600;'>{total_mobility:.1f} / 8.0</span>", unsafe_allow_html=True)
            else:
                total_mobility = 0
            
            # Use stint counter to reset goals/duration after adding
            stint_key = len(st.session_state.stints)
            
            c1, c2, c3 = st.columns(3)
            with c1:
                home_goals = st.number_input(f"{home_team} Goals", min_value=0, max_value=20, value=0, key=f"home_goals_{stint_key}")
            with c2:
                away_goals = st.number_input(f"{away_team} Goals", min_value=0, max_value=20, value=0, key=f"away_goals_{stint_key}")
            with c3:
                duration = st.number_input("Duration (min)", min_value=0.5, max_value=10.0, value=2.0, step=0.5, key=f"duration_{stint_key}")
            
            can_add = len(selected_players) == 4 and total_mobility <= 8.0
            if st.button("✅ Add Stint", disabled=not can_add, type="primary", use_container_width=True):
                add_stint(selected_players, home_goals, away_goals, duration)
                st.rerun()
        
        # Recorded Stints
        with st.expander("📋 Recorded Stints", expanded=len(st.session_state.stints) > 0):
            if st.session_state.stints:
                for s in st.session_state.stints:
                    lineup_display = ", ".join([format_player_name(p) for p in sorted(s['lineup'])])
                    st.markdown(f"""
                    <div style="padding: 0.5rem; background: #f9fafb; border-radius: 0.375rem; margin-bottom: 0.5rem; font-size: 0.875rem;">
                        <strong>Stint {s['stint_num']}</strong>: {lineup_display}<br>
                        <span style="color: #6b7280;">Score: {s['home_goals']}-{s['away_goals']} | {s['duration']} min</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="empty-state">No stints recorded yet</div>', unsafe_allow_html=True)
        
        # Metrics
        total_time = sum(s['duration'] for s in st.session_state.stints)
        st.markdown(f"""
        <div class="metrics-row">
            <div class="metric-card">
                <div class="metric-label">Total Stints</div>
                <div class="metric-value">{len(st.session_state.stints)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Time Played</div>
                <div class="metric-value">{total_time:.1f} min</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Goal Diff</div>
                <div class="metric-value">{goal_diff}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Player Minutes
        with st.expander("⏱️ Player Minutes"):
            if st.session_state.player_minutes:
                for p, m in sorted(st.session_state.player_minutes.items(), key=lambda x: -x[1]):
                    penalty = (1 - calculate_fatigue_penalty(m)) * 100
                    st.markdown(f"**{format_player_name(p)}**: {m:.1f} min (-{penalty:.0f}% fatigue)")
            else:
                st.markdown("No players have played yet.")
    
    # RIGHT: Lineup Recommendation
    with col_right:
        st.markdown("""
        <div class="section-header">
            <div class="section-indicator indicator-rose"></div>
            <div class="section-title">Lineup Recommendation</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Strategy Badge
        offensive_weight = calculate_offensive_weight(goal_diff)
        defensive_weight = 1 - offensive_weight
        
        st.markdown(f"""
        <div class="strategy-container">
            <div class="strategy-badge">BALANCED</div>
            <div class="strategy-weights">
                Offensive Weight: {offensive_weight*100:.0f}% | Defensive Weight: {defensive_weight*100:.0f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Get Optimal Lineup Button
        if st.button("🎯 Get Optimal Lineup", type="primary", use_container_width=True):
            with st.spinner("Running optimization..."):
                try:
                    selected, off_weight = get_optimal_lineup(
                        team=home_team,
                        goal_diff=goal_diff,
                        player_minutes=st.session_state.player_minutes if st.session_state.player_minutes else None
                    )
                    st.session_state.optimal_result = {
                        'selected': selected,
                        'off_weight': off_weight
                    }
                except Exception as e:
                    st.error(f"Optimization failed: {e}")
        
        # Recommended Players
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-header">Recommended Players</div>', unsafe_allow_html=True)
        
        if st.session_state.optimal_result:
            result = st.session_state.optimal_result
            selected = result['selected']
            
            # Sort by classification descending
            selected_sorted = selected.sort_values('mobility_rating', ascending=False)
            
            for idx, (_, row) in enumerate(selected_sorted.iterrows(), 1):
                minutes = st.session_state.player_minutes.get(row['player'], 0)
                st.markdown(f"""
                <div class="player-card">
                    <div class="player-number">{idx}</div>
                    <div class="player-info">
                        <div class="player-name">{format_player_name(row['player'])}</div>
                        <div class="player-stats">
                            Class: {row['mobility_rating']} | O: {row['O_posterior']:.1f} | D: {row['D_posterior']:.1f} | Min: {minutes:.1f}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            total_class = selected['mobility_rating'].sum()
            total_offense = selected['O_posterior'].sum()
            total_defense = selected['D_posterior'].sum()
            
            st.markdown(f"""
            <div class="stats-row">
                <div>
                    <div class="stat-label">Total Class</div>
                    <div class="stat-value">{total_class:.1f}</div>
                </div>
                <div>
                    <div class="stat-label">Offense</div>
                    <div class="stat-value blue">{total_offense:.1f}</div>
                </div>
                <div>
                    <div class="stat-label">Defense</div>
                    <div class="stat-value green">{total_defense:.1f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-state">Click "Get Optimal Lineup" to see recommendations</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Model Explanation (minimal)
        with st.expander("📖 How the Model Works"):
            st.markdown("""
            **RAPM Ratings**: Measures player impact on scoring differential. Each player has offensive and defensive ratings.
            
            **Fatigue Model**: Players lose effectiveness with more minutes played.
            
            **Dynamic Weighting**: Adjusts offensive vs defensive priorities based on score differential.
            
            **Lineup Optimization**: Evaluates all valid 4-player lineups (classification ≤ 8.0) and recommends the best.
            """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Reset button at bottom
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Reset Game", use_container_width=True):
            reset_game()
            st.rerun()


if __name__ == "__main__":
    main()
