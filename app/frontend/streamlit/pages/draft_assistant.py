import os
import sys
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.grid import grid

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

# Enhanced Custom CSS for professional responsive design
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables for consistent theming */
    :root {
        --primary-mocha: #9E7A68;
        --secondary-cream: #F5F1EB;
        --accent-terracotta: #C4956C;
        --accent-sage: #8B9A7A;
        --accent-charcoal: #4A4A4A;
        --light-cream: #FDFCFA;
        --medium-beige: #E8E0D6;
        --dark-brown: #6B5B4F;
        --text-dark: #2D2520;
        --success-green: #7A8B6C;
        --warning-amber: #D4A574;
        --error-rust: #B85450;
        --border-radius: 12px;
        --shadow-light: 0 2px 8px rgba(158, 122, 104, 0.12);
        --shadow-medium: 0 4px 16px rgba(158, 122, 104, 0.18);
        --shadow-heavy: 0 8px 32px rgba(158, 122, 104, 0.24);
    }
    
    /* Global font family */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main app background */
    .stApp {
        background: linear-gradient(135deg, var(--light-cream) 0%, var(--secondary-cream) 100%);
    }
    
    /* Main container improvements */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
        margin: 0 auto;
        background: rgba(255, 255, 255, 0.7);
        border-radius: var(--border-radius);
        box-shadow: var(--shadow-light);
        backdrop-filter: blur(10px);
    }
    
    /* Header styling */
    h1 {
        color: var(--text-dark);
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, var(--primary-mocha), var(--secondary-cream));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h2 {
        color: var(--text-dark);
        font-weight: 600;
        font-size: 1.8rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    h3 {
        color: var(--text-dark);
        font-weight: 600;
        font-size: 1.4rem;
        margin-bottom: 1rem;
    }
    
    /* Enhanced button styling */
    .stButton > button {
        width: 100%;
        border-radius: var(--border-radius);
        border: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: var(--shadow-light);
        font-family: 'Inter', sans-serif;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary-mocha) 0%, var(--secondary-cream) 100%);
        color: white;
        border: 2px solid transparent;
    }
    
    .stButton > button[kind="secondary"] {
        background: white;
        color: var(--primary-mocha);
        border: 2px solid var(--primary-mocha);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-medium);
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, var(--secondary-cream) 0%, var(--primary-mocha) 100%);
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: var(--primary-mocha);
        color: white;
    }
    
    /* Enhanced dataframe styling */
    .stDataFrame {
        border-radius: var(--border-radius);
        overflow: hidden;
        box-shadow: var(--shadow-light);
        border: 1px solid var(--medium-beige);
        background: white;
    }
    
    .stDataFrame > div {
        border-radius: var(--border-radius);
        background: white;
    }
    
    /* Table header styling */
    .stDataFrame thead th {
        background: linear-gradient(135deg, var(--primary-mocha), var(--accent-terracotta));
        color: white;
        font-weight: 600;
        padding: 1rem 0.75rem;
        border-bottom: 2px solid var(--dark-brown);
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    
    .stDataFrame tbody td {
        padding: 0.75rem;
        border-bottom: 1px solid var(--medium-beige);
        background: white;
    }
    
    .stDataFrame tbody tr:hover {
        background-color: rgba(158, 122, 104, 0.08);
    }
    
    /* Metric cards styling */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid var(--medium-beige);
        padding: 1.5rem;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow-light);
        transition: all 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        box-shadow: var(--shadow-medium);
        transform: translateY(-2px);
        border-color: var(--primary-mocha);
    }
    
    [data-testid="metric-container"] > div {
        color: var(--text-dark);
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-mocha);
    }
    
    [data-testid="metric-container"] [data-testid="metric-label"] {
        font-size: 0.9rem;
        font-weight: 500;
        color: var(--dark-brown);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Alert/info box styling */
    .stAlert {
        border-radius: var(--border-radius);
        border: none;
        box-shadow: var(--shadow-light);
        padding: 1rem 1.5rem;
    }
    
    .stAlert[data-baseweb="notification"] {
        border-left: 4px solid var(--primary-mocha);
    }
    
    .stSuccess {
        background: linear-gradient(135deg, rgba(122, 139, 108, 0.1), rgba(122, 139, 108, 0.05));
        border-left: 4px solid var(--success-green) !important;
    }
    
    .stInfo {
        background: linear-gradient(135deg, rgba(216, 191, 175, 0.1), rgba(216, 191, 175, 0.05));
        border-left: 4px solid var(--primary-mocha) !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--secondary-cream) 0%, var(--light-cream) 100%);
        border-right: 2px solid var(--medium-beige);
    }
    
    /* Sidebar container */
    .css-1d391kg .block-container {
        background: transparent;
    }
    
    .css-1d391kg .stSelectbox > div > div {
        border-radius: var(--border-radius);
        border: 2px solid var(--medium-beige);
        transition: border-color 0.3s ease;
        background: white;
    }
    
    .css-1d391kg .stSelectbox > div > div:focus-within {
        border-color: var(--primary-mocha);
        box-shadow: 0 0 0 3px rgba(158, 122, 104, 0.1);
    }
    
    .css-1d391kg .stNumberInput > div > div {
        border-radius: var(--border-radius);
        border: 2px solid var(--medium-beige);
        transition: border-color 0.3s ease;
        background: white;
    }
    
    .css-1d391kg .stNumberInput > div > div:focus-within {
        border-color: var(--primary-mocha);
        box-shadow: 0 0 0 3px rgba(158, 122, 104, 0.1);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, var(--light-cream), white);
        border-radius: var(--border-radius);
        border: 1px solid var(--medium-beige);
        padding: 1rem;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, var(--medium-beige), var(--light-cream));
        box-shadow: var(--shadow-light);
    }
    
    .streamlit-expanderContent {
        border: 1px solid var(--medium-beige);
        border-top: none;
        border-radius: 0 0 var(--border-radius) var(--border-radius);
        padding: 1.5rem;
        background: white;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: var(--light-cream);
        padding: 0.5rem;
        border-radius: var(--border-radius);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary-mocha);
        color: white;
    }
    
    /* Card-like containers */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow-light);
        border: 1px solid var(--medium-beige);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        box-shadow: var(--shadow-medium);
        transform: translateY(-2px);
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 1rem;
        }
        
        h1 {
            font-size: 2rem;
        }
        
        h2 {
            font-size: 1.5rem;
        }
        
        h3 {
            font-size: 1.2rem;
        }
        
        .stButton > button {
            padding: 0.6rem 1rem;
            font-size: 0.9rem;
        }
        
        [data-testid="metric-container"] {
            padding: 1rem;
        }
        
        [data-testid="metric-container"] [data-testid="metric-value"] {
            font-size: 1.5rem;
        }
        
        /* Stack columns on mobile */
        .element-container .stColumns {
            flex-direction: column;
        }
        
        .css-1d391kg {
            width: 100%;
        }
    }
    
    @media (max-width: 480px) {
        h1 {
            font-size: 1.8rem;
        }
        
        .stButton > button {
            padding: 0.5rem 0.8rem;
            font-size: 0.85rem;
        }
        
        [data-testid="metric-container"] {
            padding: 0.75rem;
        }
    }
    
    /* Loading and transition effects */
    .stSpinner > div {
        border-top-color: var(--primary-mocha) !important;
    }
    
    /* Custom utility classes */
    .gradient-bg {
        background: linear-gradient(135deg, var(--light-cream) 0%, var(--medium-beige) 100%);
        padding: 1.5rem;
        border-radius: var(--border-radius);
        margin-bottom: 2rem;
        border: 1px solid var(--medium-beige);
    }
    
    .highlight-box {
        background: linear-gradient(135deg, rgba(216, 191, 175, 0.1), rgba(245, 241, 235, 0.05));
        border: 1px solid rgba(216, 191, 175, 0.2);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--light-cream);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-mocha);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--secondary-cream);
    }
</style>
""", unsafe_allow_html=True)

# Apply metric card styling
style_metric_cards(
    background_color="#FFFFFF",
    border_left_color="#9E7A68",
    border_color="#E8E0D6",
    box_shadow="#F0F2F6"
)

# Title and description with better spacing
st.markdown("""
<div style="background: linear-gradient(135deg, var(--primary-mocha), var(--dark-brown)); 
            padding: 2rem; border-radius: var(--border-radius); margin-bottom: 2rem; 
            color: white; box-shadow: var(--shadow-medium);">
    <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
        🏀 The Lineup - Draft Assistant
    </h1>
    <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.95; color: var(--light-cream);">
        Your AI-powered fantasy basketball draft companion
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="highlight-box">
    <h4 style="margin-top: 0; color: var(--text-dark);">🎯 Welcome to The Lineup!</h4>
    <p style="margin-bottom: 0; color: var(--dark-brown); font-size: 1.1rem; line-height: 1.6;">
        This advanced draft assistant uses z-score analysis and real-time player projections 
        to help you dominate your fantasy basketball draft. Get optimal pick suggestions, 
        track team compositions, and make data-driven decisions.
    </p>
</div>
""", unsafe_allow_html=True)

# Draft Type Selection with improved styling
with st.sidebar:
    st.markdown("""
    <div style="background: linear-gradient(135deg, var(--primary-mocha), var(--dark-brown)); 
                padding: 1rem; border-radius: var(--border-radius); margin-bottom: 1rem; 
                color: white; box-shadow: var(--shadow-light);">
        <h3 style="margin: 0; font-size: 1.2rem; color: white;">⚙️ Draft Configuration</h3>
        <p style="margin: 0.25rem 0 0 0; font-size: 0.9rem; opacity: 0.9; color: var(--light-cream);">Set up your draft parameters</p>
    </div>
    """, unsafe_allow_html=True)
    
    draft_type = st.selectbox(
        "🎯 Draft Type",
        ["Mock Draft", "Live Draft Assistant", "Draft Optimizer"],
        help="Choose how you want to use the draft assistant"
    )

    # Season Selection
    season = st.selectbox(
        "📅 Season",
        ["2023-24"],
        help="Select the NBA season for draft analysis"
    )

    st.markdown("---")
    
    # League Settings with better organization
    st.markdown("""
    <div style="background: linear-gradient(135deg, var(--accent-sage), var(--dark-brown)); 
                padding: 1rem; border-radius: var(--border-radius); margin-bottom: 1rem; 
                color: white; box-shadow: var(--shadow-light);">
        <h3 style="margin: 0; font-size: 1.2rem; color: white;">🏆 League Settings</h3>
        <p style="margin: 0.25rem 0 0 0; font-size: 0.9rem; opacity: 0.9; color: var(--light-cream);">Configure your league parameters</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_sidebar1, col_sidebar2 = st.columns(2)
    with col_sidebar1:
        num_teams = st.number_input("👥 Teams", min_value=8, max_value=20, value=12)
    with col_sidebar2:
        draft_position = st.number_input("📍 Your Pick", min_value=1, max_value=num_teams, value=1)

# Main content based on draft type
if draft_type == "Mock Draft":
    st.markdown("""
    <div style="background: linear-gradient(135deg, var(--primary-mocha), var(--dark-brown)); 
                padding: 1.5rem; border-radius: var(--border-radius); margin-bottom: 2rem; 
                color: white; box-shadow: var(--shadow-medium);">
        <h2 style="margin: 0; font-size: 2rem; color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.3);">🎯 Mock Draft Mode</h2>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.95; color: var(--light-cream);">Practice drafting against AI opponents</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize or continue draft
    if "draft_started" not in st.session_state:
        st.session_state.draft_started = False
    
    if not st.session_state.draft_started:
        # Pre-draft layout - enhanced with grid
        my_grid = grid(2, 2, 2, 1, vertical_align="center")
        
        # Main content area
        my_grid.markdown("""
        ### 🚀 Ready to Start Your Mock Draft?
        
        Practice your draft strategy against AI-powered opponents that simulate real draft behavior. 
        Our advanced algorithm considers:
        
        - **Z-Score Rankings** - Statistical player value analysis
        - **Position Scarcity** - Smart positional drafting
        - **Team Needs** - Balanced roster construction
        - **ADP Trends** - Real draft position data
        """)
        
        my_grid.markdown("""
        ### 📊 What You'll Get:
        
        - Real-time player recommendations
        - Team composition analysis  
        - Z-score breakdowns by category
        - Draft position optimization
        """)
        
        # Start button with enhanced styling
        if my_grid.button("🏀 Start Mock Draft", type="primary", use_container_width=True):
            st.session_state.draft_started = True
            st.rerun()
            
        my_grid.markdown("*Get ready to dominate your real draft!*")
    
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

        # Query: Get players with season-specific team data
        player_pool_query = """
        SELECT *
        FROM (
            SELECT DISTINCT ON (p.player_id)
                p.player_id,
                p.name,
                COALESCE(ps.team, p.team) as team,
                p.position,
                pf.total_z_score,
                psi.adp,
                p.injury_notes
            FROM players p
            JOIN player_features pf ON p.player_id = pf.player_id AND pf.season = %s
            LEFT JOIN player_stats ps ON p.player_id = ps.player_id AND ps.season = %s
            LEFT JOIN player_season_info psi ON p.player_id = psi.player_id AND psi.season = pf.season
            ORDER BY p.player_id, pf.total_z_score DESC
        ) sub
        ORDER BY total_z_score DESC
        """
        player_pool_df = pd.read_sql(player_pool_query, engine, params=(season, season))
        player_pool_df = player_pool_df.rename(columns={
            'name': 'name',
            'team': 'team', 
            'position': 'position',
            'total_z_score': 'total_z_score',
            'adp': 'adp',
            'injury_notes': 'injury_notes'
        })

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

            # Check if we have available players
            if len(available_players) == 0:
                st.session_state.draft_complete = True
                st.rerun()

            # --- 3. Player Selection Interface ---
            if current_team == user_team:
                st.success(f"🎯 Your pick! (Round {st.session_state.draft_round}, Pick {current_team})")
                
                # Player selection in responsive layout
                col_pick1, col_pick2 = st.columns([3, 1])
                with col_pick1:
                    player_options = available_players[["player_id", "name"]].drop_duplicates()
                    player_dict = dict(zip(player_options["name"], player_options["player_id"]))
                    selected_name = st.selectbox("🏀 Select a player to draft:", player_options["name"])
                with col_pick2:
                    st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
                    if st.button("✅ Draft Player", key=f"draft_{selected_name}", type="primary"):
                        pid = player_dict[selected_name]
                        st.session_state.team_rosters[user_team].append(pid)
                        st.session_state.drafted_players.append(pid)
                        st.session_state.status_message = f"You drafted {selected_name}!"
                        # Advance to next pick
                        advance_pick()
                        st.rerun()
            else:
                # AI pick: auto-draft top available player by z-score (fast)
                ai_team = current_team
                if len(available_players) > 0:
                    ai_pick = available_players.iloc[0]
                    st.session_state.team_rosters[ai_team].append(ai_pick["player_id"])
                    st.session_state.drafted_players.append(ai_pick["player_id"])
                    st.session_state.status_message = f"🤖 Team {ai_team} drafted {ai_pick['name']}!"
                    # Advance to next pick
                    advance_pick()
                    st.rerun()
                else:
                    # No more players available
                    st.session_state.draft_complete = True
                    st.rerun()

            # --- 4. Roster & Team Displays ---
            if st.session_state.status_message:
                st.info(st.session_state.status_message)
            
            # Show user roster immediately after any change
            st.markdown("### 👥 Your Team Roster")
            user_roster_ids = st.session_state.team_rosters[user_team]
            if user_roster_ids:
                user_roster_df = player_pool_df[player_pool_df["player_id"].isin(user_roster_ids)]
                # Show condensed view for mobile
                st.dataframe(
                    user_roster_df[["name", "team", "position", "total_z_score"]].rename(columns={
                        'name': 'Player',
                        'team': 'Team', 
                        'position': 'Pos',
                        'total_z_score': 'Z-Score'
                    }), 
                    use_container_width=True,
                    hide_index=True
                )
                
                # Show roster summary
                col_summary1, col_summary2, col_summary3 = st.columns(3)
                with col_summary1:
                    st.metric("Players Drafted", len(user_roster_ids))
                with col_summary2:
                    avg_z_score = user_roster_df['total_z_score'].mean()
                    st.metric("Avg Z-Score", f"{avg_z_score:.2f}")
                with col_summary3:
                    total_z_score = user_roster_df['total_z_score'].sum()
                    st.metric("Total Z-Score", f"{total_z_score:.2f}")
            else:
                st.info("No players drafted yet.")
            
            # Available Players Section with improved mobile layout
            st.markdown("---")  # Visual separator
            st.markdown("### 🔥 Top Available Players")
            top_available = available_players.head(20)
            
            # Enhanced table with more stats
            display_df = top_available.rename(columns={
                'name': 'Player',
                'team': 'Team',
                'position': 'Position',
                'total_z_score': 'Total Z-Score',
                'adp': 'ADP',
                'injury_notes': 'Injury Notes'
            })
            
            # Get detailed stats for top available players
            if len(top_available) > 0:
                top_player_ids = top_available['player_id'].tolist()
                detailed_stats_query = """
                SELECT DISTINCT ON (ps.player_id)
                    ps.player_id,
                    ps.points_per_game,
                    ps.rebounds_per_game,
                    ps.assists_per_game,
                    ps.steals_per_game,
                    ps.blocks_per_game,
                    ps.turnovers_per_game,
                    ps.fg_pct,
                    ps.ft_pct,
                    ps.three_pm,
                    ps.games_played,
                    pf.z_points,
                    pf.z_rebounds,
                    pf.z_assists,
                    pf.z_steals,
                    pf.z_blocks,
                    pf.z_turnovers,
                    pf.z_fg_pct,
                    pf.z_ft_pct,
                    pf.z_three_pm
                FROM player_stats ps
                JOIN player_features pf ON ps.player_id = pf.player_id AND ps.season = pf.season
                WHERE ps.season = %s AND ps.player_id = ANY(%s)
                ORDER BY ps.player_id
                """
                stats_df = pd.read_sql(detailed_stats_query, engine, params=(season, top_player_ids))
                
                # Merge stats with display data - ensure no duplicates
                enhanced_df = display_df.merge(stats_df, on='player_id', how='left').drop_duplicates(subset=['player_id'])
                
                # Show basic table first
                st.dataframe(
                    display_df[["Player", "Team", "Position", "Total Z-Score", "ADP"]],
                    use_container_width=True,
                    hide_index=True
                )
                
                # Add detailed stats expander
                with st.expander("📊 View Detailed Player Stats & Z-Scores"):
                    if not stats_df.empty:
                        # Create tabs for better mobile experience
                        tab1, tab2 = st.tabs(["📈 Season Averages", "⚡ Z-Score Breakdown"])
                        
                        with tab1:
                            detailed_display = enhanced_df[[
                                'Player', 'Team', 'Position',
                                'points_per_game', 'rebounds_per_game', 'assists_per_game',
                                'steals_per_game', 'blocks_per_game', 'turnovers_per_game',
                                'fg_pct', 'ft_pct', 'three_pm', 'games_played'
                            ]].rename(columns={
                                'points_per_game': 'PPG',
                                'rebounds_per_game': 'RPG', 
                                'assists_per_game': 'APG',
                                'steals_per_game': 'SPG',
                                'blocks_per_game': 'BPG',
                                'turnovers_per_game': 'TPG',
                                'fg_pct': 'FG%',
                                'ft_pct': 'FT%',
                                'three_pm': '3PM',
                                'games_played': 'GP'
                            })
                            
                            st.dataframe(detailed_display, use_container_width=True, hide_index=True)
                        
                        with tab2:
                            z_score_display = enhanced_df[[
                                'Player', 'Team',
                                'z_points', 'z_rebounds', 'z_assists',
                                'z_steals', 'z_blocks', 'z_turnovers',
                                'z_fg_pct', 'z_ft_pct', 'z_three_pm', 'Total Z-Score'
                            ]].rename(columns={
                                'z_points': 'Z-PTS',
                                'z_rebounds': 'Z-REB',
                                'z_assists': 'Z-AST',
                                'z_steals': 'Z-STL',
                                'z_blocks': 'Z-BLK',
                                'z_turnovers': 'Z-TO',
                                'z_fg_pct': 'Z-FG%',
                                'z_ft_pct': 'Z-FT%',
                                'z_three_pm': 'Z-3PM'
                            })
                            
                            st.dataframe(z_score_display, use_container_width=True, hide_index=True)
                    else:
                        st.write("No detailed stats available for these players.")
            else:
                st.dataframe(
                    display_df[["Player", "Team", "Position", "Total Z-Score", "ADP"]],
                    use_container_width=True,
                    hide_index=True
                )

            # Responsive roster layout
            st.markdown("---")  # Visual separator
            
            # Use different layouts for mobile vs desktop
            roster_col1, roster_col2 = st.columns([2, 1])
            
            with roster_col1:
                st.markdown("### 🏆 All Teams")
                with st.expander("View All Team Rosters"):
                    for tid, roster in st.session_state.team_rosters.items():
                        st.markdown(f"**Team {tid}{' (You)' if tid == user_team else ''}:**")
                        if roster:
                            team_df = player_pool_df[player_pool_df["player_id"].isin(roster)]
                            st.dataframe(
                                team_df[["name", "position", "total_z_score"]].rename(columns={
                                    'name': 'Player',
                                    'position': 'Pos',
                                    'total_z_score': 'Z-Score'
                                }), 
                                use_container_width=True, 
                                hide_index=True
                            )
                        else:
                            st.write("No players drafted yet.")
            
            with roster_col2:
                st.markdown("### ⏱️ Draft Status")
                if current_team == user_team:
                    st.success("🎯 Your turn to pick!")
                else:
                    st.info(f"🤖 Team {current_team} is picking...")
                
                # Show current round and pick info
                st.metric("Current Round", st.session_state.draft_round)
                st.metric("Current Pick", f"Team {current_team}")
                
                # Show next user pick in round
                user_picks_in_round = [i for i, t in enumerate(st.session_state.draft_order, 1) if t == user_team]
                if user_picks_in_round and current_team != user_team:
                    next_user_pick = user_picks_in_round[0]
                    st.metric("Your Next Pick", f"#{next_user_pick} in round")

            # --- 5. Draft Progress Sidebar ---
            with st.sidebar:
                st.markdown("---")
                st.markdown("""
                <div style="background: linear-gradient(135deg, var(--accent-charcoal), var(--dark-brown)); 
                            padding: 1rem; border-radius: var(--border-radius); margin-bottom: 1rem; color: white;">
                    <h3 style="margin: 0; font-size: 1.2rem;">📊 Draft Progress</h3>
                    <p style="margin: 0.25rem 0 0 0; font-size: 0.9rem; opacity: 0.9;">Track your draft status</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Use columns for better mobile sidebar layout
                sidebar_col1, sidebar_col2 = st.columns(2)
                with sidebar_col1:
                    st.metric("🔄 Round", st.session_state.draft_round)
                with sidebar_col2:
                    st.metric("🎯 Current Pick", st.session_state.current_pick_team)
                
                # Find user's next pick
                picks_left = [i for i, t in enumerate(st.session_state.draft_order) if t == user_team]
                if picks_left:
                    st.metric("⏭️ Your Next Pick", picks_left[0] + 1)

            # --- 6. Check for Draft Completion ---
            if is_draft_complete():
                st.session_state.draft_complete = True
                st.experimental_rerun()

        # --- Draft Complete: Show Summary ---
        else:
            st.success("🎉 Draft complete! Here are the final rosters:")
            
            # Create tabs for final summary
            team_tabs = st.tabs([f"Team {i}" + (" (You)" if i == st.session_state.user_team_id else "") 
                                for i in range(1, num_teams + 1)])
            
            for i, tab in enumerate(team_tabs, 1):
                with tab:
                    roster = st.session_state.team_rosters[i]
                    if roster:
                        team_df = player_pool_df[player_pool_df["player_id"].isin(roster)]
                        st.dataframe(
                            team_df[["name", "team", "position", "total_z_score"]].rename(columns={
                                'name': 'Player',
                                'team': 'Team',
                                'position': 'Position',
                                'total_z_score': 'Z-Score'
                            }), 
                            use_container_width=True, 
                            hide_index=True
                        )
                    else:
                        st.write("No players drafted.")

elif draft_type == "Live Draft Assistant":
    st.markdown("""
    <div style="background: linear-gradient(135deg, var(--error-rust), var(--warning-amber)); 
                padding: 1.5rem; border-radius: var(--border-radius); margin-bottom: 2rem; color: white;">
        <h2 style="margin: 0; font-size: 2rem;">🔴 Live Draft Assistant</h2>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">Real-time draft support for your live draft</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="highlight-box">
        <h4 style="margin-top: 0; color: var(--text-dark);">🚧 Coming Soon!</h4>
        <p style="margin-bottom: 0.5rem; color: var(--dark-brown);">
            Connect this assistant to your live draft to get real-time pick suggestions
            and team analysis as your draft progresses.
        </p>
        <p style="margin-bottom: 0; color: var(--dark-brown); font-size: 0.9rem;">
            <strong>Features in development:</strong><br>
            • Real-time draft room integration<br>
            • Live pick tracking and suggestions<br>
            • Opponent team analysis<br>
            • Dynamic strategy adjustments
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.file_uploader("📁 Upload Custom ADP (Optional)", type=["csv"], help="Upload your league's custom ADP data")

elif draft_type == "Draft Optimizer":
    st.markdown("""
    <div style="background: linear-gradient(135deg, var(--accent-terracotta), var(--warning-amber)); 
                padding: 1.5rem; border-radius: var(--border-radius); margin-bottom: 2rem; color: white;">
        <h2 style="margin: 0; font-size: 2rem;">⚡ Draft Optimizer</h2>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">Advanced strategy planning and optimization</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        st.selectbox("🎯 Optimization Strategy", ["Balanced", "Punt FT%", "Punt FG%", "Punt TO"])
    with col_opt2:
        st.selectbox("📈 Focus Categories", ["All Categories", "Counting Stats", "Percentages", "Custom"])

# Footer with improved styling
with st.sidebar:
    st.markdown("---")
    if "draft_started" in st.session_state and st.session_state.draft_started and not st.session_state.get('draft_complete', False):
        st.markdown("""
        <div style="background: linear-gradient(135deg, var(--accent-charcoal), var(--dark-brown)); 
                    padding: 1rem; border-radius: var(--border-radius); margin-bottom: 1rem; color: white;">
            <h3 style="margin: 0; font-size: 1.2rem;">🎯 Quick Stats</h3>
            <p style="margin: 0.25rem 0 0 0; font-size: 0.9rem; opacity: 0.9;">Draft overview</p>
        </div>
        """, unsafe_allow_html=True)
        sidebar_col1, sidebar_col2 = st.columns(2)
        with sidebar_col1:
            st.metric("👥 Teams", num_teams)
        with sidebar_col2:
            st.metric("📍 Your Pos", draft_position)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; color: var(--dark-brown);">
            <small>🏀 The Lineup v1.0<br>
            Fantasy Basketball Draft Assistant</small>
        </div>
        """, unsafe_allow_html=True)    