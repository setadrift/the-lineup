import os
import sys
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from streamlit_extras.colored_header import colored_header
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
        --primary-orange: #FF6B35;
        --primary-blue: #2E86AB;
        --secondary-orange: #F7931E;
        --light-gray: #F8F9FA;
        --medium-gray: #E9ECEF;
        --dark-gray: #6C757D;
        --text-dark: #2E3440;
        --success-green: #28A745;
        --warning-yellow: #FFC107;
        --border-radius: 12px;
        --shadow-light: 0 2px 8px rgba(0,0,0,0.08);
        --shadow-medium: 0 4px 16px rgba(0,0,0,0.12);
        --shadow-heavy: 0 8px 32px rgba(0,0,0,0.16);
    }
    
    /* Global font family */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Main container improvements */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* Header styling */
    h1 {
        color: var(--text-dark);
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, var(--primary-orange), var(--secondary-orange));
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
        background: linear-gradient(135deg, var(--primary-orange) 0%, var(--secondary-orange) 100%);
        color: white;
        border: 2px solid transparent;
    }
    
    .stButton > button[kind="secondary"] {
        background: white;
        color: var(--primary-orange);
        border: 2px solid var(--primary-orange);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-medium);
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, var(--secondary-orange) 0%, var(--primary-orange) 100%);
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: var(--primary-orange);
        color: white;
    }
    
    /* Enhanced dataframe styling */
    .stDataFrame {
        border-radius: var(--border-radius);
        overflow: hidden;
        box-shadow: var(--shadow-light);
        border: 1px solid var(--medium-gray);
    }
    
    .stDataFrame > div {
        border-radius: var(--border-radius);
    }
    
    /* Table header styling */
    .stDataFrame thead th {
        background: linear-gradient(135deg, var(--light-gray), var(--medium-gray));
        color: var(--text-dark);
        font-weight: 600;
        padding: 1rem 0.75rem;
        border-bottom: 2px solid var(--primary-orange);
    }
    
    .stDataFrame tbody td {
        padding: 0.75rem;
        border-bottom: 1px solid var(--medium-gray);
    }
    
    .stDataFrame tbody tr:hover {
        background-color: rgba(255, 107, 53, 0.05);
    }
    
    /* Metric cards styling */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid var(--medium-gray);
        padding: 1.5rem;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow-light);
        transition: all 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        box-shadow: var(--shadow-medium);
        transform: translateY(-2px);
    }
    
    [data-testid="metric-container"] > div {
        color: var(--text-dark);
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-orange);
    }
    
    [data-testid="metric-container"] [data-testid="metric-label"] {
        font-size: 0.9rem;
        font-weight: 500;
        color: var(--dark-gray);
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
        border-left: 4px solid var(--primary-orange);
    }
    
    .stSuccess {
        background: linear-gradient(135deg, rgba(40, 167, 69, 0.1), rgba(40, 167, 69, 0.05));
        border-left: 4px solid var(--success-green) !important;
    }
    
    .stInfo {
        background: linear-gradient(135deg, rgba(255, 107, 53, 0.1), rgba(255, 107, 53, 0.05));
        border-left: 4px solid var(--primary-orange) !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--light-gray) 0%, white 100%);
        border-right: 1px solid var(--medium-gray);
    }
    
    .css-1d391kg .stSelectbox > div > div {
        border-radius: var(--border-radius);
        border: 2px solid var(--medium-gray);
        transition: border-color 0.3s ease;
    }
    
    .css-1d391kg .stSelectbox > div > div:focus-within {
        border-color: var(--primary-orange);
        box-shadow: 0 0 0 3px rgba(255, 107, 53, 0.1);
    }
    
    .css-1d391kg .stNumberInput > div > div {
        border-radius: var(--border-radius);
        border: 2px solid var(--medium-gray);
        transition: border-color 0.3s ease;
    }
    
    .css-1d391kg .stNumberInput > div > div:focus-within {
        border-color: var(--primary-orange);
        box-shadow: 0 0 0 3px rgba(255, 107, 53, 0.1);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, var(--light-gray), white);
        border-radius: var(--border-radius);
        border: 1px solid var(--medium-gray);
        padding: 1rem;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, var(--medium-gray), var(--light-gray));
        box-shadow: var(--shadow-light);
    }
    
    .streamlit-expanderContent {
        border: 1px solid var(--medium-gray);
        border-top: none;
        border-radius: 0 0 var(--border-radius) var(--border-radius);
        padding: 1.5rem;
        background: white;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: var(--light-gray);
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
        background: var(--primary-orange);
        color: white;
    }
    
    /* Card-like containers */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow-light);
        border: 1px solid var(--medium-gray);
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
        border-top-color: var(--primary-orange) !important;
    }
    
    /* Custom utility classes */
    .gradient-bg {
        background: linear-gradient(135deg, var(--light-gray) 0%, var(--medium-gray) 100%);
        padding: 1.5rem;
        border-radius: var(--border-radius);
        margin-bottom: 2rem;
        border: 1px solid var(--medium-gray);
    }
    
    .highlight-box {
        background: linear-gradient(135deg, rgba(255, 107, 53, 0.1), rgba(247, 147, 30, 0.05));
        border: 1px solid rgba(255, 107, 53, 0.2);
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
        background: var(--light-gray);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-orange);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--secondary-orange);
    }
    
    /* Pick Suggestions Styling */
    .suggestion-container {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-left: 4px solid var(--primary-orange);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .suggestion-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .suggestion-high-priority {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border-left-color: #f39c12;
    }
    
    .suggestion-medium-priority {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border-left-color: #17a2b8;
    }
    
    .suggestion-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-dark);
        margin-bottom: 0.25rem;
    }
    
    .suggestion-reasoning {
        font-style: italic;
        color: #6c757d;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    
    .pick-preview {
        background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%);
        border: 1px solid #c3e6cb;
        border-radius: 6px;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
    
    .pick-preview strong {
        color: #155724;
    }
</style>
""", unsafe_allow_html=True)

# Apply metric card styling
style_metric_cards(
    background_color="#FFFFFF",
    border_left_color="#FF6B35",
    border_color="#E9ECEF",
    box_shadow="#F0F2F6"
)

# Title and description with better spacing
colored_header(
    label="🏀 The Lineup - Draft Assistant",
    description="Your AI-powered fantasy basketball draft companion",
    color_name="orange-70"
)

st.markdown("""
<div class="highlight-box">
    <h4 style="margin-top: 0; color: var(--text-dark);">🎯 Welcome to The Lineup!</h4>
    <p style="margin-bottom: 0; color: var(--dark-gray); font-size: 1.1rem; line-height: 1.6;">
        This advanced draft assistant uses z-score analysis and real-time player projections 
        to help you dominate your fantasy basketball draft. Get optimal pick suggestions, 
        track team compositions, and make data-driven decisions.
    </p>
</div>
""", unsafe_allow_html=True)

# Draft Type Selection with improved styling
with st.sidebar:
    colored_header(
        label="⚙️ Draft Configuration",
        description="Set up your draft parameters",
        color_name="blue-70"
    )
    
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
    colored_header(
        label="🏆 League Settings",
        description="Configure your league parameters",
        color_name="green-70"
    )
    
    col_sidebar1, col_sidebar2 = st.columns(2)
    with col_sidebar1:
        num_teams = st.number_input("👥 Teams", min_value=8, max_value=20, value=12)
    with col_sidebar2:
        draft_position = st.number_input("📍 Your Pick", min_value=1, max_value=num_teams, value=1)

# Main content based on draft type
if draft_type == "Mock Draft":
    colored_header(
        label="🎯 Mock Draft Mode",
        description="Practice drafting against AI opponents",
        color_name="orange-70"
    )
    
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

        # Helper: Get pick suggestions with reasoning
        def get_pick_suggestions(available_players, user_roster_ids, current_round, draft_position, num_teams):
            suggestions = []
            
            if len(available_players) == 0:
                return suggestions
            
            # Get user's current roster for analysis
            user_roster_df = player_pool_df[player_pool_df["player_id"].isin(user_roster_ids)] if user_roster_ids else pd.DataFrame()
            
            # Analyze top 10 available players
            top_players = available_players.head(10)
            
            for idx, player in top_players.iterrows():
                reasoning_parts = []
                priority_score = 0
                
                # 1. Position Scarcity Analysis
                position = player['position']
                position_available = available_players[available_players['position'].str.contains(position.split('-')[0], na=False)]
                elite_position_count = len(position_available[position_available['total_z_score'] > 5])
                
                if elite_position_count <= 3:
                    reasoning_parts.append(f"Only {elite_position_count} elite {position}s left")
                    priority_score += 15
                elif elite_position_count <= 5:
                    reasoning_parts.append(f"Limited elite {position} options remaining")
                    priority_score += 10
                
                # 2. Value vs ADP Analysis
                if pd.notna(player['adp']):
                    current_pick_number = ((current_round - 1) * num_teams) + draft_position
                    adp_value = player['adp'] - current_pick_number
                    
                    if adp_value > 12:
                        reasoning_parts.append(f"Excellent value - typically drafted {int(adp_value)} picks later")
                        priority_score += 20
                    elif adp_value > 6:
                        reasoning_parts.append(f"Good value - ADP suggests pick {int(player['adp'])}")
                        priority_score += 10
                    elif adp_value < -6:
                        reasoning_parts.append(f"Reaching early - ADP is pick {int(player['adp'])}")
                        priority_score -= 5
                
                # 3. Team Need Assessment
                if len(user_roster_df) > 0:
                    # Analyze team's category strengths/weaknesses
                    team_positions = user_roster_df['position'].str.split('-').explode().value_counts()
                    
                    # Position need
                    main_position = position.split('-')[0]
                    position_count = team_positions.get(main_position, 0)
                    
                    if position_count == 0:
                        reasoning_parts.append(f"Fills {main_position} need")
                        priority_score += 12
                    elif position_count == 1 and main_position in ['C', 'PG']:
                        reasoning_parts.append(f"Adds {main_position} depth")
                        priority_score += 8
                
                # 4. Z-Score Tier Analysis
                z_score = player['total_z_score']
                next_player_z = top_players.iloc[min(idx + 1, len(top_players) - 1)]['total_z_score'] if idx < len(top_players) - 1 else 0
                z_drop = z_score - next_player_z
                
                if z_score > 10:
                    reasoning_parts.append("Elite tier player")
                    priority_score += 15
                elif z_score > 7:
                    reasoning_parts.append("High-tier option")
                    priority_score += 10
                elif z_score > 4:
                    reasoning_parts.append("Solid contributor")
                    priority_score += 5
                
                if z_drop > 2:
                    reasoning_parts.append("Significant tier drop after this pick")
                    priority_score += 8
                
                # 5. Round-specific logic
                if current_round <= 3:
                    if z_score > 8:
                        reasoning_parts.append("Top-tier talent for early rounds")
                        priority_score += 10
                elif current_round <= 6:
                    if z_score > 5:
                        reasoning_parts.append("Strong mid-round value")
                        priority_score += 8
                else:
                    if z_score > 2:
                        reasoning_parts.append("Good late-round upside")
                        priority_score += 5
                
                # 6. Next pick timing
                picks_until_next = (num_teams * 2) - draft_position if current_round % 2 == 1 else draft_position - 1
                if picks_until_next > 20:
                    reasoning_parts.append(f"Long wait until next pick ({picks_until_next} picks)")
                    priority_score += 5
                
                # Create suggestion
                if reasoning_parts:
                    main_reason = reasoning_parts[0]
                    additional_reasons = reasoning_parts[1:3]  # Limit to avoid clutter
                    
                    suggestion = {
                        'player_name': player['name'],
                        'player_id': player['player_id'],
                        'position': player['position'],
                        'z_score': player['total_z_score'],
                        'adp': player['adp'],
                        'main_reason': main_reason,
                        'additional_reasons': additional_reasons,
                        'priority_score': priority_score,
                        'reasoning_text': f"{main_reason}" + (f" • {' • '.join(additional_reasons)}" if additional_reasons else "")
                    }
                    suggestions.append(suggestion)
            
            # Sort by priority score and return top 5
            suggestions.sort(key=lambda x: x['priority_score'], reverse=True)
            return suggestions[:5]

        # Helper: Format pick suggestion display
        def display_pick_suggestions(suggestions):
            if not suggestions:
                st.info("🤖 Analyzing available players...")
                return
            
            st.markdown("### 🎯 AI Pick Suggestions")
            
            for i, suggestion in enumerate(suggestions):
                priority_emoji = "🔥" if suggestion['priority_score'] > 25 else "⭐" if suggestion['priority_score'] > 15 else "💡"
                
                # Determine CSS class based on priority
                css_class = "suggestion-high-priority" if suggestion['priority_score'] > 25 else "suggestion-medium-priority" if suggestion['priority_score'] > 15 else "suggestion-container"
                
                # Format ADP safely
                adp_display = f"{suggestion['adp']:.0f}" if pd.notna(suggestion['adp']) else "N/A"
                
                st.markdown(f"""
                <div class="{css_class}">
                    <div class="suggestion-header">
                        {priority_emoji} {suggestion['player_name']} ({suggestion['position']})
                    </div>
                    <div class="suggestion-reasoning">
                        {suggestion['reasoning_text']}
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 0.5rem; font-size: 0.85rem;">
                        <span><strong>Z-Score:</strong> {suggestion['z_score']:.1f}</span>
                        <span><strong>ADP:</strong> {adp_display}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

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
                
                # Generate and display pick suggestions
                suggestions = get_pick_suggestions(
                    available_players, 
                    st.session_state.team_rosters[user_team], 
                    st.session_state.draft_round, 
                    draft_position, 
                    num_teams
                )
                
                if suggestions:
                    display_pick_suggestions(suggestions)
                    st.markdown("---")
                
                # Player selection in responsive layout
                col_pick1, col_pick2 = st.columns([3, 1])
                with col_pick1:
                    player_options = available_players[["player_id", "name"]].drop_duplicates()
                    player_dict = dict(zip(player_options["name"], player_options["player_id"]))
                    
                    # Pre-select the top suggestion if available
                    default_selection = suggestions[0]['player_name'] if suggestions else player_options["name"].iloc[0]
                    default_index = list(player_options["name"]).index(default_selection) if default_selection in player_options["name"].values else 0
                    
                    selected_name = st.selectbox(
                        "🏀 Select a player to draft:", 
                        player_options["name"],
                        index=default_index,
                        help="Top AI suggestion is pre-selected"
                    )
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
                        tab1, tab2, tab3 = st.tabs(["📈 Season Averages", "⚡ Z-Score Breakdown", "🔬 Advanced Stats"])
                        
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
                        
                        with tab3:
                            # Show advanced stats if available
                            advanced_cols = ['Player', 'Team', 'Position']
                            advanced_rename = {}
                            
                            # Check which advanced stats are available
                            if 'age' in enhanced_df.columns:
                                advanced_cols.append('age')
                                advanced_rename['age'] = 'Age'
                            if 'usage_rate' in enhanced_df.columns:
                                advanced_cols.append('usage_rate')
                                advanced_rename['usage_rate'] = 'Usage%'
                            if 'true_shooting_pct' in enhanced_df.columns:
                                advanced_cols.append('true_shooting_pct')
                                advanced_rename['true_shooting_pct'] = 'TS%'
                            if 'player_efficiency_rating' in enhanced_df.columns:
                                advanced_cols.append('player_efficiency_rating')
                                advanced_rename['player_efficiency_rating'] = 'PER'
                            if 'points_per_36' in enhanced_df.columns:
                                advanced_cols.extend(['points_per_36', 'rebounds_per_36', 'assists_per_36'])
                                advanced_rename.update({
                                    'points_per_36': 'PTS/36',
                                    'rebounds_per_36': 'REB/36',
                                    'assists_per_36': 'AST/36'
                                })
                            
                            if len(advanced_cols) > 3:  # More than just Player, Team, Position
                                advanced_display = enhanced_df[advanced_cols].rename(columns=advanced_rename)
                                
                                # Format percentage columns
                                for col in advanced_display.columns:
                                    if col in ['Usage%', 'TS%']:
                                        advanced_display[col] = advanced_display[col].apply(
                                            lambda x: f"{x:.1%}" if pd.notnull(x) else "N/A"
                                        )
                                    elif col in ['PER', 'PTS/36', 'REB/36', 'AST/36']:
                                        advanced_display[col] = advanced_display[col].apply(
                                            lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A"
                                        )
                                
                                st.dataframe(advanced_display, use_container_width=True, hide_index=True)
                                
                                # Add explanations
                                st.markdown("**Advanced Stats Explained:**")
                                st.markdown("- **Usage%**: Percentage of team plays used by player while on court")
                                st.markdown("- **TS%**: True Shooting % (accounts for 3-pointers and free throws)")
                                st.markdown("- **PER**: Player Efficiency Rating (league average ≈ 15)")
                                st.markdown("- **Per-36**: Stats projected to 36 minutes played")
                            else:
                                st.info("Advanced stats will be available once the enhanced feature generation is complete.")
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
                    
                    # Show preview of next suggestion
                    if st.session_state.team_rosters[user_team]:  # Only if user has drafted someone
                        preview_suggestions = get_pick_suggestions(
                            available_players, 
                            st.session_state.team_rosters[user_team], 
                            st.session_state.draft_round, 
                            draft_position, 
                            num_teams
                        )
                        
                        if preview_suggestions:
                            top_suggestion = preview_suggestions[0]
                            st.markdown(f"""
                            <div class="pick-preview">
                                <strong>💡 Next Pick Preview:</strong><br>
                                {top_suggestion['player_name']} ({top_suggestion['position']})<br>
                                <em>{top_suggestion['main_reason']}</em>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Show current round and pick info
                st.metric("🔄 Current Round", st.session_state.draft_round)
                st.metric("🎯 Current Pick", f"Team {current_team}")
                
                # Show next user pick in round
                user_picks_in_round = [i for i, t in enumerate(st.session_state.draft_order, 1) if t == user_team]
                if user_picks_in_round and current_team != user_team:
                    next_user_pick = user_picks_in_round[0]
                    st.metric("⏭️ Your Next Pick", f"#{next_user_pick} in round")

            # --- 5. Draft Progress Sidebar ---
            with st.sidebar:
                st.markdown("---")
                colored_header(
                    label="📊 Draft Progress",
                    description="Track your draft status",
                    color_name="violet-70"
                )
                
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
    colored_header(
        label="🔴 Live Draft Assistant",
        description="Real-time draft support for your live draft",
        color_name="red-70"
    )
    
    st.markdown("""
    <div class="highlight-box">
        <h4 style="margin-top: 0; color: var(--text-dark);">🚧 Coming Soon!</h4>
        <p style="margin-bottom: 0.5rem; color: var(--dark-gray);">
            Connect this assistant to your live draft to get real-time pick suggestions
            and team analysis as your draft progresses.
        </p>
        <p style="margin-bottom: 0; color: var(--dark-gray); font-size: 0.9rem;">
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
    colored_header(
        label="⚡ Draft Optimizer",
        description="Advanced strategy planning and optimization",
        color_name="blue-70"
    )
    
    st.markdown("""
    <div class="highlight-box">
        <h4 style="margin-top: 0; color: var(--text-dark);">🔬 Advanced Strategy Planning</h4>
        <p style="margin-bottom: 0.5rem; color: var(--dark-gray);">
            Plan your optimal draft strategy based on your draft position and league settings.
            The optimizer will suggest the best possible combinations of players to target.
        </p>
        <p style="margin-bottom: 0; color: var(--dark-gray); font-size: 0.9rem;">
            <strong>Optimization features:</strong><br>
            • Multi-round strategy planning<br>
            • Punt strategy recommendations<br>
            • Value-based drafting analysis<br>
            • Position scarcity modeling
        </p>
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
        colored_header(
            label="🎯 Quick Stats",
            description="Draft overview",
            color_name="gray-70"
        )
        sidebar_col1, sidebar_col2 = st.columns(2)
        with sidebar_col1:
            st.metric("👥 Teams", num_teams)
        with sidebar_col2:
            st.metric("📍 Your Pos", draft_position)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; color: var(--dark-gray);">
            <small>🏀 The Lineup v1.0<br>
            Fantasy Basketball Draft Assistant</small>
        </div>
        """, unsafe_allow_html=True) 