"""
The Lineup - Draft Assistant (Modular Version)
Clean, maintainable draft assistant with intelligent pick suggestions
"""

import os
import sys
import pandas as pd
import streamlit as st

# Setup path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
sys.path.insert(0, project_root)

# Import our modular components
from app.frontend.streamlit.utils.styling import apply_main_styling
from app.frontend.streamlit.utils.database import (
    get_player_pool, 
    get_detailed_player_stats, 
    get_player_by_ids,
    get_available_seasons,
    validate_database_connection,
    get_database_engine
)
from app.frontend.streamlit.components.ui_components import (
    setup_metric_cards,
    render_header,
    render_sidebar_config,
    render_pre_draft_screen,
    display_pick_suggestions,
    render_player_selection,
    render_roster_display,
    render_available_players,
    render_draft_status,
    render_sidebar_progress,
    render_coming_soon,
    render_onboarding_modal,
    render_help_section,
    render_feature_highlights,
    render_auto_save_controls,
    render_draft_save_notification
)
from app.frontend.streamlit.components.draft_logic import (
    DraftState,
    PickSuggestionEngine,
    AIOpponent,
    CategoryAnalyzer,
    initialize_draft_state,
    get_available_players
)


def main():
    """Main application entry point."""
    
    # Set page config for wide layout (must be first Streamlit command)
    # Only set if not already configured (e.g., when called directly vs from streamlit_app.py)
    try:
        st.set_page_config(
            page_title="The Lineup - Draft Assistant",
            page_icon="🏀",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    except st.errors.StreamlitAPIException:
        # Page config already set, continue
        pass
    
    # Apply styling
    apply_main_styling()
    setup_metric_cards()
    
    # Validate database connection
    if not validate_database_connection():
        st.error("Unable to connect to database. Please check your connection.")
        st.stop()
    
    # Show onboarding for new users
    onboarding_completed = render_onboarding_modal()
    
    # Only show main interface after onboarding is completed
    if onboarding_completed:
        # Render header
        render_header()
        
        # Show feature highlights for returning users
        render_feature_highlights()
        
        # Get available data
        available_seasons = get_available_seasons()
        draft_types = ["Mock Draft", "Live Draft Assistant", "Draft Optimizer"]
        
        # Render sidebar configuration and help
        config = render_sidebar_config(draft_types, available_seasons)
        render_help_section()
        render_auto_save_controls()
        
        # Check if we have a restored configuration
        if "restored_config" in st.session_state:
            restored_config = st.session_state.restored_config
            # Override sidebar config with restored values
            config.update(restored_config)
            # Clear the restored config so it doesn't persist
            del st.session_state.restored_config
        
        # Store current config for persistence
        st.session_state.current_draft_config = config
        
        # Route to appropriate draft mode
        if config['draft_type'] == "Mock Draft":
            handle_mock_draft(config)
        elif config['draft_type'] == "Live Draft Assistant":
            handle_live_draft_assistant()
        elif config['draft_type'] == "Draft Optimizer":
            handle_draft_optimizer()


def handle_mock_draft(config: dict):
    """Handle mock draft functionality."""
    
    # Initialize draft started state
    if "draft_started" not in st.session_state:
        st.session_state.draft_started = False
    
    if not st.session_state.draft_started:
        # Pre-draft screen
        if render_pre_draft_screen():
            st.session_state.draft_started = True
            st.rerun()
    else:
        # Load player data
        player_pool_df = get_player_pool(config['season'])
        
        if player_pool_df.empty:
            st.error("No player data available for the selected season.")
            return
        
        # Initialize draft state
        draft_state = initialize_draft_state(config['num_teams'], config['draft_position'])
        
        # Initialize suggestion engine
        suggestion_engine = PickSuggestionEngine(player_pool_df)
        
        # Check if draft is complete
        if draft_state.is_complete():
            handle_draft_complete(draft_state, player_pool_df, config['num_teams'])
            return
        
        # Get available players
        available_players = get_available_players(player_pool_df, draft_state.drafted_players)
        
        if len(available_players) == 0:
            st.session_state.draft_complete = True
            st.rerun()
        
        # Handle current pick
        if draft_state.current_pick_team == draft_state.user_team_id:
            handle_user_pick(draft_state, available_players, suggestion_engine, config)
        else:
            handle_ai_pick(draft_state, available_players)
        
        # Display draft interface
        render_draft_interface(
            draft_state, 
            available_players, 
            player_pool_df, 
            suggestion_engine, 
            config
        )


def handle_user_pick(draft_state: DraftState, available_players: pd.DataFrame, 
                    suggestion_engine: PickSuggestionEngine, config: dict):
    """Handle user's pick turn."""
    
    st.success(f"🎯 Your pick! (Round {draft_state.round}, Pick {draft_state.current_pick_team})")
    
    # Generate suggestions (now with relative team analysis)
    suggestions = suggestion_engine.get_suggestions(
        available_players,
        draft_state.get_user_roster_ids(),
        draft_state.round,
        config['draft_position'],
        config['num_teams'],
        max_suggestions=5,
        all_team_rosters=draft_state.team_rosters,
        user_team_id=draft_state.user_team_id
    )
    
    # Display suggestions
    if suggestions:
        display_pick_suggestions(suggestions)
        st.markdown("---")
    
    # Player selection interface
    selected_player = render_player_selection(available_players, suggestions)
    
    if selected_player:
        # Get player ID
        player_options = available_players[["player_id", "name"]].drop_duplicates()
        player_dict = dict(zip(player_options["name"], player_options["player_id"]))
        player_id = player_dict[selected_player]
        
        # Draft the player
        draft_state.draft_player(player_id, draft_state.user_team_id, selected_player)
        draft_state.advance_pick()
        
        # Auto-save after user pick
        render_draft_save_notification(draft_state, config)
        
        st.rerun()


def handle_ai_pick(draft_state: DraftState, available_players: pd.DataFrame):
    """Handle AI opponent's pick."""
    
    ai_pick = AIOpponent.make_pick(available_players)
    
    if ai_pick:
        draft_state.draft_player(
            ai_pick['player_id'], 
            draft_state.current_pick_team, 
            ai_pick['player_name']
        )
        draft_state.advance_pick()
        
        # Auto-save after AI pick (if enabled)
        config = st.session_state.get("current_draft_config", {})
        if config:
            render_draft_save_notification(draft_state, config)
        
        st.rerun()
    else:
        # No more players available
        draft_state.complete = True
        st.rerun()


def render_draft_interface(draft_state: DraftState, available_players: pd.DataFrame, 
                          player_pool_df: pd.DataFrame, suggestion_engine: PickSuggestionEngine, 
                          config: dict):
    """Render the main draft interface."""
    
    # Show status message
    if draft_state.status_message:
        st.info(draft_state.status_message)
    
    # Initialize category analyzer
    category_analyzer = CategoryAnalyzer(player_pool_df)
    
    # Show user roster with category analysis (now with relative rankings)
    user_roster_df = get_player_by_ids(draft_state.get_user_roster_ids(), player_pool_df)
    user_category_analysis = category_analyzer.analyze_team_categories(
        draft_state.get_user_roster_ids(), 
        draft_state.team_rosters, 
        draft_state.user_team_id
    )
    
    # Get punt strategy analysis
    punt_analysis = category_analyzer.detect_punt_strategies(
        draft_state.get_user_roster_ids(),
        draft_state.team_rosters,
        draft_state.user_team_id
    )
    
    # Get roster construction warnings
    construction_warnings = category_analyzer.detect_roster_construction_warnings(
        draft_state.get_user_roster_ids()
    )
    
    # Store construction warnings in session state for UI components
    st.session_state.construction_warnings = construction_warnings
    
    render_roster_display(user_roster_df, user_category_analysis, punt_analysis)
    
    # Available players section
    st.markdown("---")
    engine = get_database_engine()
    render_available_players(available_players, player_pool_df, config['season'], engine)
    
    # Draft status and team rosters
    st.markdown("---")
    
    roster_col1, roster_col2 = st.columns([2, 1])
    
    with roster_col1:
        st.markdown("### 🏆 All Teams")
        with st.expander("View All Team Rosters"):
            for team_id, roster_ids in draft_state.team_rosters.items():
                st.markdown(f"**Team {team_id}{' (You)' if team_id == draft_state.user_team_id else ''}:**")
                if roster_ids:
                    team_df = get_player_by_ids(roster_ids, player_pool_df)
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
        # Generate suggestions for preview
        suggestions = suggestion_engine.get_suggestions(
            available_players,
            draft_state.get_user_roster_ids(),
            draft_state.round,
            config['draft_position'],
            config['num_teams'],
            max_suggestions=5,
            all_team_rosters=draft_state.team_rosters,
            user_team_id=draft_state.user_team_id
        ) if draft_state.get_user_roster_ids() else []
        
        render_draft_status(
            draft_state.current_pick_team,
            draft_state.user_team_id,
            draft_state.round,
            suggestions
        )
        
        # Show category needs summary in sidebar (now with relative rankings)
        if draft_state.get_user_roster_ids():
            weak_categories = category_analyzer.get_priority_needs(
                draft_state.get_user_roster_ids(), 
                draft_state.team_rosters, 
                draft_state.user_team_id
            )
            
            # Filter out punt categories from priority needs
            punt_categories = [p['category'] for p in punt_analysis.get('punt_categories', [])]
            filtered_weak_categories = [cat for cat in weak_categories if cat not in punt_categories]
            
            # Show punt strategy message if detected
            if punt_analysis.get('strategy_confidence', 'none') in ['high', 'medium']:
                st.markdown("### 🎯 Draft Strategy")
                strategy_message = punt_analysis.get('message', '')
                if punt_analysis.get('strategy_confidence') == 'high':
                    st.success(f"**{strategy_message}**")
                else:
                    st.info(f"**{strategy_message}**")
            
            # Show priority needs (excluding punt categories)
            if filtered_weak_categories:
                st.markdown("### 🎯 Priority Needs")
                need_text = []
                for weak_cat in filtered_weak_categories:
                    cat_info = category_analyzer.CATEGORIES[weak_cat]
                    need_text.append(f"🔴 {cat_info['short']}")
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #dc354515, #dc354505);
                    border: 1px solid #dc354540;
                    border-left: 4px solid #dc3545;
                    border-radius: 6px;
                    padding: 0.75rem;
                    margin: 0.5rem 0;
                ">
                    <strong>Focus on:</strong><br>
                    {' • '.join([cat.split(' ', 1)[1] for cat in need_text])}
                </div>
                """, unsafe_allow_html=True)
            elif punt_categories:
                # If we have punt categories but no other needs, show punt strategy focus
                st.markdown("### 🎯 Strategy Focus")
                non_punt_cats = [cat for cat in category_analyzer.CATEGORIES.keys() if cat not in punt_categories]
                focus_text = []
                for cat in non_punt_cats[:4]:  # Show top 4 non-punt categories
                    cat_info = category_analyzer.CATEGORIES[cat]
                    focus_text.append(f"🟢 {cat_info['short']}")
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #28a74515, #28a74505);
                    border: 1px solid #28a74540;
                    border-left: 4px solid #28a745;
                    border-radius: 6px;
                    padding: 0.75rem;
                    margin: 0.5rem 0;
                ">
                    <strong>Maximize:</strong><br>
                    {' • '.join([cat.split(' ', 1)[1] for cat in focus_text])}
                </div>
                """, unsafe_allow_html=True)
    
    # Sidebar progress
    render_sidebar_progress(
        draft_state.round,
        draft_state.current_pick_team,
        draft_state.draft_order,
        draft_state.user_team_id,
        config['num_teams']
    )


def handle_draft_complete(draft_state: DraftState, player_pool_df: pd.DataFrame, num_teams: int):
    """Handle draft completion."""
    
    st.success("🎉 Draft complete! Here are the final rosters:")
    
    # Create tabs for final summary
    team_tabs = st.tabs([f"Team {i}" + (" (You)" if i == draft_state.user_team_id else "") 
                        for i in range(1, num_teams + 1)])
    
    for i, tab in enumerate(team_tabs, 1):
        with tab:
            roster_ids = draft_state.team_rosters[i]
            if roster_ids:
                team_df = get_player_by_ids(roster_ids, player_pool_df)
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


def handle_live_draft_assistant():
    """Handle live draft assistant mode."""
    
    render_coming_soon(
        "Live Draft Assistant",
        "Connect this assistant to your live draft to get real-time pick suggestions and team analysis as your draft progresses.",
        [
            "Real-time draft room integration",
            "Live pick tracking and suggestions", 
            "Opponent team analysis",
            "Dynamic strategy adjustments"
        ]
    )
    
    st.file_uploader("📁 Upload Custom ADP (Optional)", type=["csv"], help="Upload your league's custom ADP data")


def handle_draft_optimizer():
    """Handle draft optimizer mode."""
    
    render_coming_soon(
        "Advanced Strategy Planning",
        "Plan your optimal draft strategy based on your draft position and league settings. The optimizer will suggest the best possible combinations of players to target.",
        [
            "Multi-round strategy planning",
            "Punt strategy recommendations",
            "Value-based drafting analysis", 
            "Position scarcity modeling"
        ]
    )
    
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        st.selectbox("🎯 Optimization Strategy", ["Balanced", "Punt FT%", "Punt FG%", "Punt TO"])
    with col_opt2:
        st.selectbox("📈 Focus Categories", ["All Categories", "Counting Stats", "Percentages", "Custom"])


if __name__ == "__main__":
    main() 