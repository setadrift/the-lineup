import os
import sys
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Setup path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
sys.path.insert(0, project_root)

# Load DB URL
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Page config
st.set_page_config(
    page_title="The Lineup - Draft Assistant",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🏀 The Lineup - Draft Assistant")
st.markdown("""
Welcome to The Lineup's Draft Assistant! This tool will help you make optimal picks
during your fantasy basketball draft based on z-score analysis and player projections.
""")

# Draft Type Selection
st.sidebar.header("Draft Settings")
draft_type = st.sidebar.selectbox(
    "Select Draft Type",
    ["Mock Draft", "Live Draft Assistant", "Draft Optimizer"],
    help="Choose how you want to use the draft assistant"
)

# Season Selection
season = st.sidebar.selectbox(
    "Select Season",
    ["2023-24"],
    help="Select the NBA season for draft analysis"
)

# League Settings
st.sidebar.header("League Settings")
num_teams = st.sidebar.number_input("Number of Teams", min_value=8, max_value=20, value=12)
draft_position = st.sidebar.number_input("Your Draft Position", min_value=1, max_value=num_teams, value=1)

# Main content based on draft type
if draft_type == "Mock Draft":
    st.header("Mock Draft Mode")
    
    # Initialize or continue draft
    if "draft_started" not in st.session_state:
        st.session_state.draft_started = False
    
    if not st.session_state.draft_started:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            ### Start a New Mock Draft
            In this mode, you can practice drafting against AI-simulated opponents.
            The assistant will help you make optimal picks while simulating other teams' selections.
            """)
        with col2:
            if st.button("Start Mock Draft", type="primary"):
                st.session_state.draft_started = True
                st.rerun()
    
    else:
        # --- 1. Draft State Initialization ---
        if "draft_state_initialized" not in st.session_state:
            st.session_state.draft_round = 1
            st.session_state.current_pick_team = 1
            st.session_state.drafted_players = []
            st.session_state.team_rosters = {i: [] for i in range(1, num_teams + 1)}
            st.session_state.user_team_id = draft_position
            # Serpentine order for the round
            st.session_state.draft_order = list(range(1, num_teams + 1))
            st.session_state.draft_state_initialized = True
            st.session_state.draft_complete = False
            st.session_state.status_message = ""

        # Query: Top 50 available players for the selected season
        player_pool_query = """
        SELECT *
        FROM (
            SELECT DISTINCT ON (p.player_id)
                p.player_id,
                p.name,
                p.team,
                p.position,
                pf.total_z_score,
                psi.adp,
                p.injury_notes
            FROM players p
            JOIN player_features pf ON p.player_id = pf.player_id AND pf.season = %s
            LEFT JOIN player_season_info psi ON p.player_id = psi.player_id AND psi.season = pf.season
            ORDER BY p.player_id, pf.total_z_score DESC
        ) sub
        ORDER BY total_z_score DESC
        LIMIT 50
        """
        player_pool_df = pd.read_sql(player_pool_query, engine, params=(season,))

        # Helper: Get available players (not drafted)
        def get_available_players():
            drafted = st.session_state.drafted_players
            return player_pool_df[~player_pool_df["player_id"].isin(drafted)]

        # Helper: Advance to next pick (serpentine logic)
        def advance_pick():
            idx = st.session_state.draft_order.index(st.session_state.current_pick_team)
            if idx + 1 < len(st.session_state.draft_order):
                st.session_state.current_pick_team = st.session_state.draft_order[idx + 1]
            else:
                # End of round: increment round, reverse order
                st.session_state.draft_round += 1
                st.session_state.draft_order = st.session_state.draft_order[::-1]
                st.session_state.current_pick_team = st.session_state.draft_order[0]

        # Helper: Check if draft is complete
        def is_draft_complete():
            # Assume 13 roster spots per team (customize as needed)
            roster_size = 13
            return all(len(roster) >= roster_size for roster in st.session_state.team_rosters.values())

        # --- 2. Draft Turn Logic ---
        if not st.session_state.draft_complete:
            available_players = get_available_players()
            current_team = st.session_state.current_pick_team
            user_team = st.session_state.user_team_id
            roster_size = 13

            # --- 3. Player Selection Interface ---
            if current_team == user_team:
                st.success(f"Your pick! (Round {st.session_state.draft_round}, Pick {current_team})")
                # Only show undrafted players
                player_options = available_players[["player_id", "name"]].drop_duplicates()
                player_dict = dict(zip(player_options["name"], player_options["player_id"]))
                selected_name = st.selectbox("Select a player to draft:", player_options["name"])
                if st.button("Draft Player", key=f"draft_{selected_name}"):
                    pid = player_dict[selected_name]
                    st.session_state.team_rosters[user_team].append(pid)
                    st.session_state.drafted_players.append(pid)
                    st.session_state.status_message = f"You drafted {selected_name}!"
                    # Advance to next pick
                    advance_pick()
                    st.rerun()
            else:
                # AI pick: auto-draft top available player by z-score
                ai_team = current_team
                ai_pick = available_players.iloc[0]
                st.session_state.team_rosters[ai_team].append(ai_pick["player_id"])
                st.session_state.drafted_players.append(ai_pick["player_id"])
                st.session_state.status_message = f"Team {ai_team} drafted {ai_pick['name']}!"
                # Advance to next pick
                advance_pick()
                st.rerun()

            # --- 4. Roster & Team Displays ---
            st.info(st.session_state.status_message)
            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader("Your Team Roster")
                user_roster_ids = st.session_state.team_rosters[user_team]
                if user_roster_ids:
                    user_roster_df = player_pool_df[player_pool_df["player_id"].isin(user_roster_ids)]
                    st.dataframe(user_roster_df[["name", "team", "position", "total_z_score", "adp", "injury_notes"]], use_container_width=True)
                else:
                    st.write("No players drafted yet.")
            with col2:
                with st.expander("View All Team Rosters"):
                    for tid, roster in st.session_state.team_rosters.items():
                        st.markdown(f"**Team {tid}{' (You)' if tid == user_team else ''}:**")
                        if roster:
                            team_df = player_pool_df[player_pool_df["player_id"].isin(roster)]
                            st.dataframe(team_df[["name", "team", "position", "total_z_score"]], use_container_width=True, hide_index=True)
                        else:
                            st.write("No players drafted yet.")

            # --- 5. Draft Progress Sidebar ---
            st.sidebar.metric("Round", st.session_state.draft_round)
            st.sidebar.metric("Current Pick", st.session_state.current_pick_team)
            # Find user's next pick
            picks_left = [i for i, t in enumerate(st.session_state.draft_order) if t == user_team]
            if picks_left:
                st.sidebar.metric("Your Next Pick", picks_left[0] + 1)

            # --- 6. Check for Draft Completion ---
            if is_draft_complete():
                st.session_state.draft_complete = True
                st.experimental_rerun()

        # --- Draft Complete: Show Summary ---
        else:
            st.success("Draft complete! Here are the final rosters:")
            for tid, roster in st.session_state.team_rosters.items():
                st.markdown(f"**Team {tid}{' (You)' if tid == st.session_state.user_team_id else ''}:**")
                team_df = player_pool_df[player_pool_df["player_id"].isin(roster)]
                st.dataframe(team_df[["name", "team", "position", "total_z_score"]], use_container_width=True, hide_index=True)
            # TODO: Add team comparison/analysis here

elif draft_type == "Live Draft Assistant":
    st.header("Live Draft Assistant Mode")
    st.markdown("""
    ### Live Draft Setup
    Connect this assistant to your live draft to get real-time pick suggestions
    and team analysis as your draft progresses.
    """)
    
    # TODO: Add ADP upload option
    st.file_uploader("Upload Custom ADP (Optional)", type=["csv"])

elif draft_type == "Draft Optimizer":
    st.header("Draft Optimizer Mode")
    st.markdown("""
    ### Draft Strategy Optimizer
    Plan your optimal draft strategy based on your draft position and league settings.
    The optimizer will suggest the best possible combinations of players to target.
    """)
    
    # TODO: Add optimization parameters
    st.selectbox("Optimization Strategy", ["Balanced", "Punt FT%", "Punt FG%", "Punt TO"])

# Footer with stats
st.sidebar.markdown("---")
st.sidebar.markdown("### Draft Progress")
if "draft_started" in st.session_state and st.session_state.draft_started:
    st.sidebar.metric("Round", "1")
    st.sidebar.metric("Pick", "1")
    st.sidebar.metric("Next Pick", f"#{draft_position * 2}") 