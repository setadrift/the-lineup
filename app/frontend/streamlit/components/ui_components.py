"""
The Lineup - UI Components
Reusable Streamlit interface components for the draft assistant
"""

import pandas as pd
import streamlit as st
from typing import List, Dict, Any, Optional
from streamlit_extras.colored_header import colored_header
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.grid import grid
from datetime import datetime


def setup_metric_cards():
    """Apply metric card styling."""
    style_metric_cards(
        background_color="#FFFFFF",
        border_left_color="#FF6B35",
        border_color="#E9ECEF",
        box_shadow="#F0F2F6"
    )


def render_header():
    """Render the main page header."""
    colored_header(
        label="🏀 The Lineup - Draft Assistant",
        description="Your AI-powered fantasy basketball draft companion",
        color_name="orange-70"
    )
    
    st.markdown("""
    <div class="highlight-box">
        <h4 style="margin-top: 0; color: var(--text-dark);">🎯 Welcome to The Lineup!</h4>
        <p style="margin-bottom: 0; color: var(--dark-gray); font-size: 1.1rem; line-height: 1.6;">
            This advanced draft assistant uses z-score analysis, player comparison tools, and historical trend analysis 
            to help you dominate your fantasy basketball draft. Get optimal pick suggestions, compare players side-by-side, 
            track team compositions, and make data-driven decisions with comprehensive analytics.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_config(draft_types: List[str], seasons: List[str]) -> Dict[str, Any]:
    """
    Render sidebar configuration options.
    
    Args:
        draft_types: List of available draft types
        seasons: List of available seasons
        
    Returns:
        Dictionary with configuration values
    """
    with st.sidebar:
        colored_header(
            label="⚙️ Draft Configuration",
            description="Set up your draft parameters",
            color_name="blue-70"
        )
        
        draft_type = st.selectbox(
            "🎯 Draft Type",
            draft_types,
            help="Choose how you want to use the draft assistant"
        )

        season = st.selectbox(
            "📅 Season",
            seasons,
            help="Select the NBA season for draft analysis"
        )

        st.markdown("---")
        
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
    
    return {
        'draft_type': draft_type,
        'season': season,
        'num_teams': num_teams,
        'draft_position': draft_position
    }


def render_saved_drafts_section():
    """
    Render saved drafts management section.
    """
    from app.frontend.streamlit.utils.persistence import DraftPersistence, restore_draft_state_to_session
    
    saved_drafts = DraftPersistence.get_saved_drafts()
    
    if saved_drafts:
        st.markdown("### 💾 Resume Saved Draft")
        
        # Create a nice display for saved drafts
        for save_state in saved_drafts:
            # Parse timestamp for display
            try:
                save_time = datetime.fromisoformat(save_state.timestamp)
                time_display = save_time.strftime("%b %d, %Y at %I:%M %p")
            except:
                time_display = "Unknown time"
            
            # Calculate progress
            total_picks = save_state.num_teams * save_state.roster_size
            picks_made = len(save_state.drafted_players)
            progress_pct = (picks_made / total_picks) * 100 if total_picks > 0 else 0
            
            # Create expandable card for each save
            with st.expander(f"🏀 {save_state.num_teams}-Team Draft (Pick {save_state.draft_position}) - {progress_pct:.0f}% Complete"):
                col_info, col_actions = st.columns([2, 1])
                
                with col_info:
                    st.markdown(f"""
                    **Draft Details:**
                    - **Season:** {save_state.season}
                    - **Teams:** {save_state.num_teams}
                    - **Your Position:** {save_state.draft_position}
                    - **Current Round:** {save_state.round}
                    - **Progress:** {picks_made}/{total_picks} picks ({progress_pct:.0f}%)
                    - **Saved:** {time_display}
                    """)
                    
                    if save_state.complete:
                        st.success("✅ Draft Complete")
                    elif save_state.current_pick_team == save_state.user_team_id:
                        st.info("🎯 Your turn to pick!")
                    else:
                        st.info(f"🤖 Team {save_state.current_pick_team}'s turn")
                
                with col_actions:
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if st.button(f"🔄 Resume Draft", key=f"resume_{save_state.draft_id}", type="primary", use_container_width=True):
                        if restore_draft_state_to_session(save_state):
                            st.success("Draft restored successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to restore draft")
                    
                    if st.button(f"🗑️ Delete Save", key=f"delete_{save_state.draft_id}", use_container_width=True):
                        if DraftPersistence.delete_draft_save(save_state.draft_id):
                            st.success("Draft deleted")
                            st.rerun()
                        else:
                            st.error("Failed to delete draft")
        
        st.markdown("---")
    
    return len(saved_drafts) > 0


def render_auto_save_controls():
    """
    Render auto-save controls in sidebar.
    """
    from app.frontend.streamlit.utils.persistence import DraftPersistence
    
    with st.sidebar:
        st.markdown("---")
        
        with st.expander("💾 Save Settings"):
            # Auto-save toggle
            auto_save = st.checkbox(
                "🔄 Auto-save draft progress",
                value=DraftPersistence.auto_save_enabled(),
                help="Automatically save your draft after each pick"
            )
            DraftPersistence.set_auto_save(auto_save)
            
            # Manual save button (if in draft)
            if st.session_state.get("draft_started", False) and not st.session_state.get("draft_complete", False):
                if st.button("💾 Save Draft Now", use_container_width=True):
                    # Get current config
                    config = st.session_state.get("current_draft_config", {})
                    draft_state = st.session_state.get("draft_state")
                    
                    if draft_state and config:
                        from app.frontend.streamlit.utils.persistence import DraftPersistence
                        draft_id = DraftPersistence.save_draft_state(draft_state, config)
                        if draft_id:
                            st.success(f"Draft saved! ID: {draft_id[:8]}")
                        else:
                            st.error("Failed to save draft")
            
            # Cleanup old saves
            if st.button("🧹 Clean Old Saves", help="Remove saves older than 7 days"):
                DraftPersistence.cleanup_old_saves()
                st.success("Old saves cleaned up")


def render_draft_save_notification(draft_state, config: Dict[str, Any]):
    """
    Show save notification after picks.
    
    Args:
        draft_state: Current draft state
        config: Draft configuration
    """
    from app.frontend.streamlit.utils.persistence import DraftPersistence
    
    # Auto-save if enabled
    if DraftPersistence.auto_save_enabled():
        draft_id = DraftPersistence.save_draft_state(draft_state, config)
        if draft_id:
            st.toast(f"✅ Draft auto-saved", icon="💾")


def render_pre_draft_screen() -> bool:
    """
    Render the pre-draft setup screen with saved drafts option.
    
    Returns:
        True if user wants to start draft, False otherwise
    """
    # Check for saved drafts first
    has_saved_drafts = render_saved_drafts_section()
    
    # Original pre-draft content
    my_grid = grid(2, 2, 2, 1, vertical_align="center")
    
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
    
    start_draft = my_grid.button("🏀 Start New Draft", type="primary", use_container_width=True)
    my_grid.markdown("*Get ready to dominate your real draft!*")
    
    return start_draft


def display_pick_suggestions(suggestions: List[Dict[str, Any]]):
    """
    Display AI pick suggestions with reasoning.
    
    Args:
        suggestions: List of suggestion dictionaries
    """
    if not suggestions:
        st.info("🤖 Analyzing available players...")
        return
    
    st.markdown("### 🎯 AI Pick Suggestions")
    
    for suggestion in suggestions:
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


def display_pick_preview(suggestion: Dict[str, Any]):
    """
    Display a pick preview for when it's not the user's turn.
    
    Args:
        suggestion: Top suggestion dictionary
    """
    st.markdown(f"""
    <div class="pick-preview">
        <strong>💡 Next Pick Preview:</strong><br>
        {suggestion['player_name']} ({suggestion['position']})<br>
        <em>{suggestion['main_reason']}</em>
    </div>
    """, unsafe_allow_html=True)


def render_player_selection(available_players: pd.DataFrame, suggestions: List[Dict[str, Any]]) -> Optional[str]:
    """
    Render player selection interface.
    
    Args:
        available_players: DataFrame of available players
        suggestions: List of pick suggestions
        
    Returns:
        Selected player name or None
    """
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
        draft_clicked = st.button("✅ Draft Player", key=f"draft_{selected_name}", type="primary")
    
    return selected_name if draft_clicked else None


def render_category_indicators(category_analysis: Dict[str, Any]):
    """
    Render category need indicators with color-coded status and team rankings.
    
    Args:
        category_analysis: Dictionary from CategoryAnalyzer.analyze_team_categories()
    """
    if not category_analysis:
        st.info("Draft players to see category analysis")
        return
    
    st.markdown("### 📊 Category Analysis vs Other Teams")
    
    # Create responsive grid for categories
    col1, col2, col3 = st.columns(3)
    
    categories = list(category_analysis.items())
    
    # Split categories into 3 columns (3 categories each)
    for i, (z_col, data) in enumerate(categories):
        col = [col1, col2, col3][i % 3]
        
        with col:
            # Create a styled metric card for each category
            status_text = data['status'].title()
            
            # Format ranking display
            rank_display = ""
            if data.get('rank') and data.get('total_teams', 0) > 1:
                rank_suffix = data.get('rank_suffix', f"{data['rank']}")
                rank_display = f"<div style='font-size: 0.75rem; color: #6c757d; margin-bottom: 0.25rem;'>{rank_suffix} of {data['total_teams']} teams</div>"
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {data['color']}15, {data['color']}05);
                border: 1px solid {data['color']}40;
                border-left: 4px solid {data['color']};
                border-radius: 8px;
                padding: 0.75rem;
                margin: 0.25rem 0;
                text-align: center;
            ">
                <div style="font-size: 1.2rem; margin-bottom: 0.25rem;">
                    {data['emoji']} <strong>{data['short']}</strong>
                </div>
                <div style="font-size: 0.8rem; color: #6c757d; margin-bottom: 0.25rem;">
                    {data['name']}
                </div>
                {rank_display}
                <div style="font-size: 0.9rem; font-weight: 600; color: {data['color']};">
                    {status_text}
                </div>
                <div style="font-size: 0.75rem; color: #6c757d;">
                    Total: {data['team_total']:.1f}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Add legend with ranking explanation
    st.markdown("""
    <div style="margin-top: 1rem; padding: 0.5rem; background: #f8f9fa; border-radius: 6px; font-size: 0.8rem;">
        <strong>Team Rankings:</strong> 
        🟢 Strong (Top 1/3 of teams) • 
        🟡 Average (Middle 1/3 of teams) • 
        🔴 Weak (Bottom 1/3 of teams)
        <br><em>Rankings compare your team's total z-score vs all other teams in the draft</em>
    </div>
    """, unsafe_allow_html=True)


def render_roster_display(roster_df: pd.DataFrame, category_analysis: Dict[str, Any] = None, title: str = "👥 Your Team Roster"):
    """
    Render team roster display with optional category analysis.
    
    Args:
        roster_df: DataFrame with roster players
        category_analysis: Optional category analysis from CategoryAnalyzer
        title: Title for the roster section
    """
    st.markdown(f"### {title}")
    
    if len(roster_df) > 0:
        # Show condensed view for mobile
        st.dataframe(
            roster_df[["name", "team", "position", "total_z_score"]].rename(columns={
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
            st.metric("Players Drafted", len(roster_df))
        with col_summary2:
            avg_z_score = roster_df['total_z_score'].mean()
            st.metric("Avg Z-Score", f"{avg_z_score:.2f}")
        with col_summary3:
            total_z_score = roster_df['total_z_score'].sum()
            st.metric("Total Z-Score", f"{total_z_score:.2f}")
        
        # Show category indicators if analysis is provided
        if category_analysis:
            render_category_indicators(category_analysis)
    else:
        st.info("No players drafted yet.")


def render_available_players(available_players: pd.DataFrame, player_pool_df: pd.DataFrame, season: str, engine):
    """
    Render available players table with detailed stats.
    
    Args:
        available_players: DataFrame of available players
        player_pool_df: Full player pool DataFrame
        season: Current season
        engine: Database engine
    """
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
    
    # Show basic table first
    st.dataframe(
        display_df[["Player", "Team", "Position", "Total Z-Score", "ADP"]],
        use_container_width=True,
        hide_index=True
    )
    
    # Feature highlight callout
    st.info("💡 **New Features**: Click below to access **⚖️ Player Comparison** and **📈 Historical Trends** analysis!")
    
    # Add detailed stats expander
    with st.expander("📊 View Detailed Player Stats & Z-Scores"):
        if len(top_available) > 0:
            # Since player_pool_df already has z-scores, use it directly instead of querying again
            top_player_ids = top_available['player_id'].tolist()
            
            # Get the players with all their data from the player pool
            enhanced_players = player_pool_df[player_pool_df['player_id'].isin(top_player_ids)].copy()
            
            if not enhanced_players.empty:
                # Create tabs for better mobile experience - now with player comparison
                tab1, tab2, tab3, tab4 = st.tabs(["📈 Season Averages", "⚡ Z-Score Breakdown", "📊 Historical Trends", "⚖️ Player Comparison"])
                
                with tab1:
                    # For season averages, we need to query the database for detailed stats
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
                        ps.games_played
                    FROM player_stats ps
                    WHERE ps.season = %s AND ps.player_id = ANY(%s)
                    ORDER BY ps.player_id
                    """
                    stats_df = pd.read_sql(detailed_stats_query, engine, params=(season, top_player_ids))
                    
                    if not stats_df.empty:
                        # Merge with player names
                        detailed_display = enhanced_players[['player_id', 'name', 'team', 'position']].merge(
                            stats_df, on='player_id', how='left'
                        ).rename(columns={
                            'name': 'Player',
                            'team': 'Team',
                            'position': 'Position',
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
                        
                        st.dataframe(
                            detailed_display[['Player', 'Team', 'Position', 'PPG', 'RPG', 'APG', 'SPG', 'BPG', 'TPG', 'FG%', 'FT%', '3PM', 'GP']], 
                            use_container_width=True, 
                            hide_index=True
                        )
                    else:
                        st.write("No detailed season averages available.")
                
                with tab2:
                    # For z-scores, use the data we already have in player_pool_df
                    z_score_columns = ['z_points', 'z_rebounds', 'z_assists', 'z_steals', 'z_blocks', 'z_turnovers', 'z_fg_pct', 'z_ft_pct', 'z_three_pm']
                    
                    # Check which z-score columns actually exist in the data
                    available_z_cols = [col for col in z_score_columns if col in enhanced_players.columns]
                    
                    if available_z_cols:
                        z_score_display = enhanced_players[['name', 'team'] + available_z_cols + ['total_z_score']].rename(columns={
                            'name': 'Player',
                            'team': 'Team',
                            'z_points': 'Z-PTS',
                            'z_rebounds': 'Z-REB',
                            'z_assists': 'Z-AST',
                            'z_steals': 'Z-STL',
                            'z_blocks': 'Z-BLK',
                            'z_turnovers': 'Z-TO',
                            'z_fg_pct': 'Z-FG%',
                            'z_ft_pct': 'Z-FT%',
                            'z_three_pm': 'Z-3PM',
                            'total_z_score': 'Total Z-Score'
                        })
                        
                        st.dataframe(z_score_display, use_container_width=True, hide_index=True)
                    else:
                        st.write("Z-score data not available for these players.")
                
                with tab3:
                    # Historical trends tab - import and use our new component
                    try:
                        from app.frontend.streamlit.components.draft_historical_trends import render_draft_historical_trends_tab
                        render_draft_historical_trends_tab(top_available)
                    except ImportError as e:
                        st.error(f"Historical trends component not available: {e}")
                        st.markdown("*Historical trends analysis requires the backend API to be running.*")
                    except Exception as e:
                        st.warning("Historical trends temporarily unavailable")
                        st.markdown("*Please ensure the backend API is running at http://localhost:8000*")
                
                with tab4:
                    # Player comparison tab - import and use our new component
                    try:
                        from app.frontend.streamlit.components.player_comparison import render_player_comparison_tool
                        render_player_comparison_tool(available_players, player_pool_df, season, engine)
                    except ImportError as e:
                        st.error(f"Player comparison component not available: {e}")
                        st.markdown("*Player comparison tool requires additional dependencies.*")
                    except Exception as e:
                        st.warning("Player comparison tool temporarily unavailable")
                        st.markdown("*Please ensure all dependencies are installed and the backend API is running.*")
            else:
                st.write("No detailed stats available for these players.")


def render_draft_status(current_team: int, user_team: int, draft_round: int, suggestions: List[Dict[str, Any]] = None):
    """
    Render draft status information.
    
    Args:
        current_team: Current team picking
        user_team: User's team ID
        draft_round: Current draft round
        suggestions: Pick suggestions for preview
    """
    st.markdown("### ⏱️ Draft Status")
    
    if current_team == user_team:
        st.success("🎯 Your turn to pick!")
    else:
        st.info(f"🤖 Team {current_team} is picking...")
        
        # Show preview of next suggestion
        if suggestions:
            top_suggestion = suggestions[0]
            display_pick_preview(top_suggestion)
    
    # Show current round and pick info
    st.metric("🔄 Current Round", draft_round)
    st.metric("🎯 Current Pick", f"Team {current_team}")


def render_sidebar_progress(draft_round: int, current_pick_team: int, draft_order: List[int], user_team: int, num_teams: int):
    """
    Render draft progress in sidebar.
    
    Args:
        draft_round: Current draft round
        current_pick_team: Current team picking
        draft_order: Current draft order
        user_team: User's team ID
        num_teams: Number of teams
    """
    with st.sidebar:
        st.markdown("---")
        colored_header(
            label="📊 Draft Progress",
            description="Track your draft status",
            color_name="violet-70"
        )
        
        sidebar_col1, sidebar_col2 = st.columns(2)
        with sidebar_col1:
            st.metric("🔄 Round", draft_round)
        with sidebar_col2:
            st.metric("🎯 Current Pick", current_pick_team)
        
        # Find user's next pick
        picks_left = [i for i, t in enumerate(draft_order) if t == user_team]
        if picks_left:
            st.metric("⏭️ Your Next Pick", picks_left[0] + 1)


def render_coming_soon(feature_name: str, description: str, features: List[str]):
    """
    Render a coming soon section for future features.
    
    Args:
        feature_name: Name of the feature
        description: Description of the feature
        features: List of features in development
    """
    st.markdown(f"""
    <div class="highlight-box">
        <h4 style="margin-top: 0; color: var(--text-dark);">🚧 {feature_name} - Coming Soon!</h4>
        <p style="margin-bottom: 0.5rem; color: var(--dark-gray);">
            {description}
        </p>
        <p style="margin-bottom: 0; color: var(--dark-gray); font-size: 0.9rem;">
            <strong>Features in development:</strong><br>
            {'<br>'.join([f"• {feature}" for feature in features])}
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_onboarding_modal():
    """
    Render an onboarding modal for new users explaining how The Lineup works.
    
    Returns:
        True if user wants to skip onboarding, False to continue showing it
    """
    # Check if user has seen onboarding before
    if "onboarding_completed" not in st.session_state:
        st.session_state.onboarding_completed = False
    
    if not st.session_state.onboarding_completed:
        # Create a prominent onboarding section
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #FF6B35, #F7931E);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 8px 32px rgba(255, 107, 53, 0.3);
        ">
            <h2 style="margin: 0 0 1rem 0; color: white;">🏀 Welcome to The Lineup!</h2>
            <p style="font-size: 1.2rem; margin: 0; opacity: 0.95;">
                Your AI-powered fantasy basketball draft assistant
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create expandable how-it-works section
        with st.expander("📚 **How The Lineup Works** - Click to learn the basics!", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                ### 🎯 **Smart Pick Suggestions**
                
                - **AI-Powered Recommendations**: Get intelligent pick suggestions based on:
                  - Position scarcity analysis
                  - Value vs Average Draft Position (ADP)
                  - Your team's category needs
                  - Round-specific strategy
                
                - **Priority Scoring**: Suggestions are ranked with 🔥 (high), ⭐ (medium), 💡 (low) priority
                
                - **Real-Time Reasoning**: Each suggestion explains *why* it's recommended
                
                ### 📊 **Category Analysis**
                
                - **9-Category Tracking**: Points, Rebounds, Assists, Steals, Blocks, Turnovers, FG%, FT%, 3PM
                
                - **Team Rankings**: See where you rank vs other teams (1st, 2nd, 3rd, etc.)
                
                - **Color-Coded Status**: 🟢 Strong (top 1/3) • 🟡 Average (middle 1/3) • 🔴 Weak (bottom 1/3)
                
                ### ⚖️ **Player Comparison Tool**
                
                - **Side-by-Side Analysis**: Compare any two players with interactive radar charts
                
                - **Z-Score Visualization**: See exactly how players stack up across all 9 categories
                
                - **Draft Recommendations**: Get intelligent insights on which player to target
                
                - **Historical Trends**: Compare player trajectories over multiple seasons
                """)
            
            with col2:
                st.markdown("""
                ### 🧠 **Z-Score Analysis**
                
                - **Statistical Ranking**: Players ranked by z-score (standard deviations above/below average)
                
                - **Multi-Category Value**: Total z-score combines all 9 fantasy categories
                
                - **Tier-Based Drafting**: Identify when there's a significant drop-off in talent
                
                ### 📈 **Historical Stat Trends**
                
                - **Multi-Season Analysis**: View player performance trends over the last 3 seasons
                
                - **Trend Indicators**: See if players are improving, declining, or staying consistent
                
                - **Draft Insights**: Make informed decisions based on player trajectory
                
                - **Mini-Sparklines**: Quick visual representation of key stat trends
                
                ### 🤖 **Mock Draft Features**
                
                - **AI Opponents**: Practice against intelligent computer opponents
                
                - **Serpentine Draft**: Realistic snake draft order (1-12, then 12-1, etc.)
                
                - **Live Updates**: Category analysis updates after each pick
                
                - **Team Comparison**: View all team rosters and see how you stack up
                """)
            
            st.markdown("---")
            
            # Advanced features callout
            st.markdown("""
            ### 🚀 **Advanced Analytics Features**
            
            **📊 Player Details Tabs** - Access comprehensive player analysis:
            - **📈 Season Averages**: Current season per-game statistics
            - **⚡ Z-Score Breakdown**: Statistical rankings across all categories  
            - **📊 Historical Trends**: Multi-season performance analysis with trend indicators
            - **⚖️ Player Comparison**: Side-by-side comparison tool with radar charts and recommendations
            
            💡 **Pro Tip**: Use the Player Comparison tool to decide between similar players or compare your targets!
            """)
            
            st.markdown("---")
            
            # Quick start guide
            st.markdown("""
            ### 🚀 **Quick Start Guide**
            
            1. **Configure Your Draft** (sidebar):
               - Choose "Mock Draft" to practice
               - Select your season (2022-23 recommended)
               - Set number of teams (8-20)
               - Pick your draft position
            
            2. **Start Drafting**:
               - Click "🏀 Start Mock Draft" 
               - Follow AI suggestions or pick your own players
               - Watch your category rankings update in real-time
            
            3. **Use Advanced Analytics**:
               - Click "📊 View Detailed Player Stats" to access all analysis tabs
               - Compare players using the ⚖️ Player Comparison tool
               - Check 📈 Historical Trends to see player trajectories
               - Focus on 🔴 weak categories to improve team balance
            
            4. **Make Strategic Decisions**:
               - Consider position scarcity (limited elite Centers, etc.)
               - Balance value picks with team needs
               - Use comparison tool for tough decisions
            
            5. **Learn & Improve**:
               - Try different draft positions and strategies
               - Use insights for your real draft!
            """)
            
            # Action buttons
            col_action1, col_action2, col_action3 = st.columns([1, 2, 1])
            
            with col_action2:
                if st.button("✅ Got it! Let's start drafting", type="primary", use_container_width=True):
                    st.session_state.onboarding_completed = True
                    st.rerun()
                
                if st.button("⏭️ Skip tutorial", use_container_width=True):
                    st.session_state.onboarding_completed = True
                    st.rerun()
        
        return False  # Continue showing onboarding
    
    return True  # Onboarding completed


def render_help_section():
    """
    Render a help section that can be accessed anytime.
    """
    with st.sidebar:
        st.markdown("---")
        
        with st.expander("❓ Need Help?"):
            st.markdown("""
            **🎯 Pick Suggestions**
            - 🔥 = High priority pick
            - ⭐ = Good option  
            - 💡 = Decent value
            
            **📊 Category Colors**
            - 🟢 = Top 1/3 of teams
            - 🟡 = Middle 1/3 of teams
            - 🔴 = Bottom 1/3 of teams
            
            **📊 Player Analysis Tabs**
            - 📈 Season Averages
            - ⚡ Z-Score Breakdown  
            - 📊 Historical Trends
            - ⚖️ Player Comparison
            
            **💡 Pro Tips**
            - Draft elite players early (rounds 1-3)
            - Address 🔴 weak categories
            - Use ⚖️ comparison for tough decisions
            - Check 📈 trends for player trajectory
            - Consider position scarcity
            """)
            
            col_help1, col_help2 = st.columns(2)
            with col_help1:
                if st.button("🔄 Show Tutorial", use_container_width=True):
                    st.session_state.onboarding_completed = False
                    st.rerun()
            
            with col_help2:
                if st.button("🧹 Reset App", use_container_width=True):
                    # Clear all session state for fresh start
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()


def render_feature_highlights():
    """
    Render feature highlights for users who completed onboarding.
    """
    if st.session_state.get("onboarding_completed", False):
        # Show a condensed feature reminder
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(255, 107, 53, 0.1), rgba(247, 147, 30, 0.05));
            border: 1px solid rgba(255, 107, 53, 0.2);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div><strong>🎯 AI Suggestions</strong> • <strong>⚖️ Player Comparison</strong> • <strong>📈 Historical Trends</strong> • <strong>📊 Team Rankings</strong></div>
                <div style="font-size: 0.8rem; color: #6c757d;">
                    <em>New to The Lineup? Check the sidebar help section!</em>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True) 