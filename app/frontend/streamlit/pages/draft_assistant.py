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
        # Mock draft in progress UI
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Available Players")
            # TODO: Add player pool table with rankings
            
        with col2:
            st.subheader("Your Team")
            # TODO: Add your team's roster and stats

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