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
    Render player selection interface with confirmation button.
    
    Args:
        available_players: DataFrame of available players
        suggestions: List of pick suggestions
        
    Returns:
        Selected player name if confirmed, None otherwise
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
            help="Browse players and click 'Draft Player' to confirm your selection"
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


def render_punt_strategy_analysis(punt_analysis: Dict[str, Any]):
    """
    Render punt strategy detection and recommendations.
    
    Args:
        punt_analysis: Dictionary from CategoryAnalyzer.detect_punt_strategies()
    """
    if not punt_analysis or punt_analysis.get('strategy_confidence', 'none') == 'none':
        return
    
    confidence = punt_analysis.get('strategy_confidence', 'none')
    punt_categories = punt_analysis.get('punt_categories', [])
    message = punt_analysis.get('message', '')
    
    if confidence in ['high', 'medium']:
        st.markdown("### 🎯 Detected Punt Strategy")
        
        # Color based on confidence
        if confidence == 'high':
            st.success(f"**{message}**")
            confidence_color = "#28a745"
        else:
            st.info(f"**{message}**")
            confidence_color = "#17a2b8"
        
        # Show punt categories
        if punt_categories:
            punt_details = []
            for punt_cat in punt_categories:
                cat_info = punt_cat.get('category_info', {})
                short_name = cat_info.get('short', punt_cat.get('category', ''))
                confidence_text = punt_cat.get('confidence', 'medium')
                punt_details.append(f"• {short_name} ({confidence_text} confidence)")
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(23, 162, 184, 0.1), rgba(23, 162, 184, 0.05));
                border: 1px solid rgba(23, 162, 184, 0.3);
                border-left: 4px solid {confidence_color};
                border-radius: 8px;
                padding: 1rem;
                margin: 0.5rem 0;
            ">
                <strong>Punting Categories:</strong><br>
                {chr(10).join(punt_details)}
            </div>
            """, unsafe_allow_html=True)
        
        # Show strategy recommendations
        recommendations = punt_analysis.get('recommendations', [])
        if recommendations:
            st.markdown("**Strategy Tips:**")
            for rec in recommendations:
                st.markdown(f"💡 {rec}")


def render_roster_construction_warnings(construction_warnings: Dict[str, Any]):
    """
    Render roster construction warnings and recommendations.
    
    Args:
        construction_warnings: Dictionary from CategoryAnalyzer.detect_roster_construction_warnings()
    """
    if not construction_warnings or not construction_warnings.get('warnings'):
        # Show positive message if no warnings
        if construction_warnings.get('risk_level') == 'none':
            st.markdown("### ✅ Roster Health Check")
            st.success("**Solid roster construction - no major concerns detected**")
        return
    
    warnings = construction_warnings.get('warnings', [])
    risk_level = construction_warnings.get('risk_level', 'low')
    message = construction_warnings.get('message', '')
    
    # Header based on risk level
    if risk_level == 'high':
        st.markdown("### ⚠️ Roster Construction Warnings")
        st.error(f"**{message}**")
        header_color = "#dc3545"
    elif risk_level == 'medium':
        st.markdown("### 💡 Roster Construction Notes")
        st.warning(f"**{message}**")
        header_color = "#ffc107"
    else:
        st.markdown("### 📋 Roster Construction Tips")
        st.info(f"**{message}**")
        header_color = "#17a2b8"
    
    # Group warnings by type for better organization
    warning_groups = {}
    for warning in warnings:
        warning_type = warning.get('type', 'other')
        if warning_type not in warning_groups:
            warning_groups[warning_type] = []
        warning_groups[warning_type].append(warning)
    
    # Display warnings by group
    for warning_type, type_warnings in warning_groups.items():
        for warning in type_warnings:
            severity = warning.get('severity', 'low')
            title = warning.get('title', 'Warning')
            warning_message = warning.get('message', '')
            recommendation = warning.get('recommendation', '')
            affected_players = warning.get('affected_players', [])
            
            # Color based on severity
            if severity == 'high':
                border_color = "#dc3545"
                bg_color = "rgba(220, 53, 69, 0.1)"
                icon = "🚨"
            elif severity == 'medium':
                border_color = "#ffc107"
                bg_color = "rgba(255, 193, 7, 0.1)"
                icon = "⚠️"
            else:
                border_color = "#17a2b8"
                bg_color = "rgba(23, 162, 184, 0.1)"
                icon = "💡"
            
            # Build affected players text
            players_text = ""
            if affected_players:
                if len(affected_players) <= 3:
                    players_text = f"<br><em>Affected: {', '.join(affected_players)}</em>"
                else:
                    players_text = f"<br><em>Affected: {', '.join(affected_players[:3])} +{len(affected_players)-3} more</em>"
            
            st.markdown(f"""
            <div style="
                background: {bg_color};
                border: 1px solid {border_color}40;
                border-left: 4px solid {border_color};
                border-radius: 8px;
                padding: 1rem;
                margin: 0.5rem 0;
            ">
                <strong>{icon} {title}</strong><br>
                {warning_message}<br>
                <span style="color: #6c757d; font-style: italic;">💡 {recommendation}</span>
                {players_text}
            </div>
            """, unsafe_allow_html=True)
    
    # Show summary statistics
    high_count = construction_warnings.get('high_severity_count', 0)
    medium_count = construction_warnings.get('medium_severity_count', 0)
    total_count = construction_warnings.get('total_warnings', 0)
    
    if total_count > 1:
        st.markdown(f"""
        <div style="
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 0.75rem;
            margin-top: 1rem;
            font-size: 0.9rem;
            text-align: center;
        ">
            <strong>Summary:</strong> {total_count} total warnings
            {f' • {high_count} high priority' if high_count > 0 else ''}
            {f' • {medium_count} medium priority' if medium_count > 0 else ''}
        </div>
        """, unsafe_allow_html=True)


def render_roster_display(roster_df: pd.DataFrame, category_analysis: Dict[str, Any], 
                         punt_analysis: Dict[str, Any] = None):
    """
    Render the user's roster with category analysis and strategic insights.
    
    Args:
        roster_df: DataFrame of user's roster
        category_analysis: Dictionary from CategoryAnalyzer.analyze_team_categories()
        punt_analysis: Dictionary from CategoryAnalyzer.detect_punt_strategies()
    """
    st.markdown("### 👥 Your Team")
    
    if roster_df.empty:
        st.info("No players drafted yet. Start building your team!")
        return
    
    # Display roster table
    display_columns = ["name", "team", "position", "total_z_score"]
    if "games_played" in roster_df.columns:
        display_columns.append("games_played")
    
    column_mapping = {
        'name': 'Player',
        'team': 'Team', 
        'position': 'Pos',
        'total_z_score': 'Z-Score',
        'games_played': 'GP'
    }
    
    # Filter and rename columns
    available_columns = [col for col in display_columns if col in roster_df.columns]
    display_df = roster_df[available_columns].rename(columns=column_mapping)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # Category analysis and strategic insights
    col_analysis1, col_analysis2 = st.columns(2)
    
    with col_analysis1:
        # Category strengths and weaknesses
        render_category_indicators(category_analysis)
        
        # Punt strategy analysis
        if punt_analysis:
            render_punt_strategy_analysis(punt_analysis)
    
    with col_analysis2:
        # Roster construction warnings
        if len(roster_df) >= 3:  # Only show warnings if we have enough players
            # We need to get the construction warnings from the CategoryAnalyzer
            # This will be passed from the main draft interface
            construction_warnings = st.session_state.get('construction_warnings', {})
            if construction_warnings:
                render_roster_construction_warnings(construction_warnings)


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
                        st.error(f"Historical trends error: {str(e)}")
                        st.markdown(f"*Error details: {type(e).__name__}: {str(e)}*")
                        # Show traceback for debugging
                        import traceback
                        st.code(traceback.format_exc())
                
                with tab4:
                    # Player comparison tab - import and use our new component
                    try:
                        from app.frontend.streamlit.components.player_comparison import render_player_comparison_tool
                        render_player_comparison_tool(available_players, player_pool_df, season, engine)
                    except ImportError as e:
                        st.error(f"Player comparison component not available: {e}")
                        st.markdown("*Player comparison tool requires additional dependencies.*")
                    except Exception as e:
                        st.error(f"Player comparison tool error: {str(e)}")
                        st.markdown(f"*Error details: {type(e).__name__}: {str(e)}*")
                        # Show traceback for debugging
                        import traceback
                        st.code(traceback.format_exc())
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


def render_draft_recap_analytics(analytics_data: Dict[str, Any]):
    """
    Render comprehensive draft recap analytics dashboard.
    
    Args:
        analytics_data: Dictionary from DraftAnalytics.generate_draft_recap()
    """
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
        <h1 style="margin: 0 0 1rem 0; color: white;">📊 Draft Recap Analytics</h1>
        <p style="font-size: 1.2rem; margin: 0; opacity: 0.95;">
            Comprehensive post-draft analysis and team projections
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Extract data
    team_analyses = analytics_data.get('team_analyses', {})
    league_stats = analytics_data.get('league_stats', {})
    league_insights = analytics_data.get('league_insights', {})
    competitive_balance = analytics_data.get('competitive_balance', {})
    strategic_insights = analytics_data.get('strategic_insights', {})
    user_team_id = analytics_data.get('user_team_id', 1)
    
    # Create main dashboard tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏆 League Overview", 
        "📊 Team Projections", 
        "⚖️ Competitive Balance", 
        "🎯 Strategic Analysis",
        "📈 Advanced Metrics"
    ])
    
    with tab1:
        render_league_overview(league_stats, league_insights, competitive_balance, user_team_id)
    
    with tab2:
        render_team_projections(team_analyses, user_team_id)
    
    with tab3:
        render_competitive_balance_analysis(competitive_balance, team_analyses)
    
    with tab4:
        render_strategic_analysis(strategic_insights, team_analyses, user_team_id)
    
    with tab5:
        render_advanced_metrics_dashboard(team_analyses, league_insights)


def render_league_overview(league_stats: Dict[str, Any], league_insights: Dict[str, Any], 
                          competitive_balance: Dict[str, Any], user_team_id: int):
    """Render league overview section."""
    
    st.markdown("### 🏆 League Overview")
    
    # Key league metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🏀 Total Teams", 
            league_stats.get('teams', 0)
        )
    
    with col2:
        st.metric(
            "📋 Total Picks", 
            league_stats.get('total_picks', 0)
        )
    
    with col3:
        st.metric(
            "🔄 Rounds", 
            league_stats.get('rounds_completed', 0)
        )
    
    with col4:
        competitiveness = competitive_balance.get('competitiveness', 'Unknown')
        balance_score = competitive_balance.get('balance_score', 0)
        st.metric(
            "⚖️ League Balance", 
            competitiveness,
            f"{balance_score:.0f}/100"
        )
    
    st.markdown("---")
    
    # League standings and insights
    col_standings, col_insights = st.columns([1, 1])
    
    with col_standings:
        st.markdown("#### 🥇 League Standings")
        
        user_standing = league_insights.get('user_standing', {})
        league_leaders = league_insights.get('league_leaders', {})
        
        if user_standing:
            user_rank = user_standing.get('rank', 'N/A')
            total_teams = user_standing.get('total_teams', 0)
            percentile = user_standing.get('percentile', 0)
            
            # User team highlight
            if user_rank == 1:
                rank_color = "#28a745"
                rank_emoji = "🥇"
            elif user_rank <= 3:
                rank_color = "#ffc107"
                rank_emoji = "🥈" if user_rank == 2 else "🥉"
            elif percentile >= 50:
                rank_color = "#17a2b8"
                rank_emoji = "📈"
            else:
                rank_color = "#dc3545"
                rank_emoji = "📉"
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {rank_color}15, {rank_color}05);
                border: 1px solid {rank_color}40;
                border-left: 4px solid {rank_color};
                border-radius: 8px;
                padding: 1rem;
                margin: 0.5rem 0;
            ">
                <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;">
                    {rank_emoji} <strong>Your Team Ranking</strong>
                </div>
                <div style="font-size: 1rem;">
                    <strong>#{user_rank}</strong> out of {total_teams} teams<br>
                    <em>{percentile:.0f}th percentile</em>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # League leaders
        if league_leaders:
            best_team = league_leaders.get('best_team', 'N/A')
            best_score = league_leaders.get('best_score', 0)
            worst_team = league_leaders.get('worst_team', 'N/A')
            worst_score = league_leaders.get('worst_score', 0)
            
            st.markdown(f"""
            **🏆 League Champion:** Team {best_team} ({best_score:.0f} pts)  
            **📉 Needs Work:** Team {worst_team} ({worst_score:.0f} pts)
            """)
    
    with col_insights:
        st.markdown("#### 📊 League Averages")
        
        league_averages = league_insights.get('league_averages', {})
        
        if league_averages:
            avg_total_z = league_averages.get('total_z_score', 0)
            avg_player_z = league_averages.get('avg_z_score_per_player', 0)
            avg_projection = league_averages.get('projection_score', 0)
            
            st.metric("📈 Avg Team Z-Score", f"{avg_total_z:.1f}")
            st.metric("👤 Avg Player Z-Score", f"{avg_player_z:.2f}")
            st.metric("🎯 Avg Projection", f"{avg_projection:.0f}/100")
        
        # Category leaders
        st.markdown("#### 🏅 Category Leaders")
        category_leaders = league_insights.get('category_leaders', {})
        
        if category_leaders:
            # Show top 3 category leaders
            leader_display = []
            for i, (cat, leader_info) in enumerate(list(category_leaders.items())[:3]):
                team_id = leader_info.get('team_id', 'N/A')
                cat_name = leader_info.get('category_name', cat)
                leader_display.append(f"**{cat_name}:** Team {team_id}")
            
            st.markdown("<br>".join(leader_display), unsafe_allow_html=True)


def render_team_projections(team_analyses: Dict[int, Dict], user_team_id: int):
    """Render team projections and grades."""
    
    st.markdown("### 📊 Team Projections & Grades")
    
    if not team_analyses:
        st.info("No team data available for analysis.")
        return
    
    # Sort teams by projection score
    sorted_teams = sorted(
        team_analyses.items(), 
        key=lambda x: x[1]['team_projection']['final_score'], 
        reverse=True
    )
    
    # Create team projection cards
    for rank, (team_id, analysis) in enumerate(sorted_teams, 1):
        team_stats = analysis.get('team_stats', {})
        team_projection = analysis.get('team_projection', {})
        position_analysis = analysis.get('position_analysis', {})
        
        is_user_team = team_id == user_team_id
        
        # Determine card styling based on grade
        grade = team_projection.get('grade', 'F')
        final_score = team_projection.get('final_score', 0)
        outlook = team_projection.get('outlook', 'Unknown')
        
        if grade.startswith('A'):
            card_color = "#28a745"
            grade_emoji = "🏆"
        elif grade.startswith('B'):
            card_color = "#17a2b8"
            grade_emoji = "📈"
        elif grade.startswith('C'):
            card_color = "#ffc107"
            grade_emoji = "⚖️"
        elif grade.startswith('D'):
            card_color = "#fd7e14"
            grade_emoji = "📉"
        else:
            card_color = "#dc3545"
            grade_emoji = "🚨"
        
        # Special styling for user team
        user_badge = " 👤 YOUR TEAM" if is_user_team else ""
        
        # Use simpler HTML structure that Streamlit can handle
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {card_color}15, {card_color}05);
            border: 1px solid {card_color}40;
            border-left: 4px solid {card_color};
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            {'border: 3px solid #FF6B35;' if is_user_team else ''}
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div style="font-size: 1.3rem; font-weight: 600;">
                    #{rank} Team {team_id}{user_badge}
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 2rem; font-weight: 700; color: {card_color};">
                        {grade_emoji} {grade}
                    </div>
                    <div style="font-size: 0.9rem; color: #6c757d;">
                        {final_score:.0f}/100 points
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Use Streamlit columns for the details instead of complex HTML grid
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **🎯 Outlook:** {outlook}  
            **👥 Roster Size:** {team_stats.get('roster_size', 0)} players  
            **📊 Total Z-Score:** {team_stats.get('total_z_score', 0):.1f}
            """)
        
        with col2:
            st.markdown(f"""
            **🏀 Top Player:** {team_stats.get('top_player', 'N/A')}  
            **⚖️ Position Balance:** {position_analysis.get('balance_score', 0):.0f}/100  
            **🔄 Flexibility:** {position_analysis.get('flexibility', 'Low')}
            """)
        
        # Summary row
        st.markdown(f"""
        <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 1rem;">
            <strong>Strengths:</strong> {team_projection.get('strong_categories', 0)} categories • 
            <strong>Weaknesses:</strong> {team_projection.get('weak_categories', 0)} categories
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")


def render_competitive_balance_analysis(competitive_balance: Dict[str, Any], team_analyses: Dict[int, Dict]):
    """Render competitive balance analysis."""
    
    st.markdown("### ⚖️ Competitive Balance Analysis")
    
    balance_score = competitive_balance.get('balance_score', 0)
    competitiveness = competitive_balance.get('competitiveness', 'Unknown')
    score_spread = competitive_balance.get('score_spread', 0)
    std_dev = competitive_balance.get('std_deviation', 0)
    
    # Balance metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "🎯 Balance Score", 
            f"{balance_score:.0f}/100",
            help="Higher scores indicate more competitive balance"
        )
    
    with col2:
        st.metric(
            "📊 Competitiveness", 
            competitiveness,
            help="Overall league competitiveness level"
        )
    
    with col3:
        st.metric(
            "📈 Score Spread", 
            f"{score_spread:.0f} pts",
            help="Difference between best and worst teams"
        )
    
    # Balance interpretation
    st.markdown("#### 📋 Balance Analysis")
    
    if balance_score >= 80:
        balance_color = "#28a745"
        balance_message = "🏆 **Excellent Balance** - This league is highly competitive with teams closely matched in strength."
    elif balance_score >= 65:
        balance_color = "#17a2b8"
        balance_message = "📈 **Good Balance** - Most teams are competitive with some clear favorites emerging."
    elif balance_score >= 50:
        balance_color = "#ffc107"
        balance_message = "⚖️ **Moderate Balance** - There's a mix of strong and weak teams with room for upsets."
    elif balance_score >= 35:
        balance_color = "#fd7e14"
        balance_message = "📉 **Poor Balance** - Clear tiers exist with some teams significantly stronger."
    else:
        balance_color = "#dc3545"
        balance_message = "🚨 **Very Poor Balance** - Highly unbalanced league with dominant teams."
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {balance_color}15, {balance_color}05);
        border: 1px solid {balance_color}40;
        border-left: 4px solid {balance_color};
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    ">
        {balance_message}
    </div>
    """, unsafe_allow_html=True)
    
    # Team distribution chart (simplified)
    if team_analyses:
        st.markdown("#### 📊 Team Score Distribution")
        
        # Create score ranges
        scores = [analysis['team_projection']['final_score'] for analysis in team_analyses.values()]
        
        # Simple distribution display
        score_ranges = {
            'Elite (80-100)': len([s for s in scores if s >= 80]),
            'Strong (70-79)': len([s for s in scores if 70 <= s < 80]),
            'Average (60-69)': len([s for s in scores if 60 <= s < 70]),
            'Weak (50-59)': len([s for s in scores if 50 <= s < 60]),
            'Poor (<50)': len([s for s in scores if s < 50])
        }
        
        for range_name, count in score_ranges.items():
            if count > 0:
                percentage = (count / len(scores)) * 100
                st.markdown(f"**{range_name}:** {count} teams ({percentage:.0f}%)")


def render_strategic_analysis(strategic_insights: Dict[str, Any], team_analyses: Dict[int, Dict], user_team_id: int):
    """Render strategic analysis and insights."""
    
    st.markdown("### 🎯 Strategic Analysis")
    
    draft_trends = strategic_insights.get('draft_trends', [])
    strategic_observations = strategic_insights.get('strategic_observations', [])
    user_recommendations = strategic_insights.get('user_recommendations', [])
    
    # Draft trends
    if draft_trends:
        st.markdown("#### 📈 Draft Trends")
        for trend in draft_trends:
            st.markdown(f"• {trend}")
    
    # Strategic observations
    if strategic_observations:
        st.markdown("#### 🔍 Strategic Observations")
        for observation in strategic_observations:
            st.markdown(f"• {observation}")
    
    # User-specific recommendations
    if user_recommendations:
        st.markdown("#### 💡 Your Team Recommendations")
        
        for i, recommendation in enumerate(user_recommendations):
            if i == 0:  # First recommendation gets special styling
                if "championship" in recommendation.lower() or "excellent" in recommendation.lower():
                    rec_color = "#28a745"
                    rec_emoji = "🏆"
                elif "strong" in recommendation.lower() or "good" in recommendation.lower():
                    rec_color = "#17a2b8"
                    rec_emoji = "💪"
                elif "solid" in recommendation.lower():
                    rec_color = "#ffc107"
                    rec_emoji = "⚖️"
                else:
                    rec_color = "#fd7e14"
                    rec_emoji = "💡"
                
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {rec_color}15, {rec_color}05);
                    border: 1px solid {rec_color}40;
                    border-left: 4px solid {rec_color};
                    border-radius: 8px;
                    padding: 1rem;
                    margin: 0.5rem 0;
                ">
                    <strong>{rec_emoji} {recommendation}</strong>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"• {recommendation}")
    
    # Punt strategy analysis across league - only show legitimate punt strategies
    st.markdown("#### 🎯 League Punt Strategy Analysis")
    
    # Filter for legitimate punt strategies only (high or medium confidence)
    punt_summary = {}
    for team_id, analysis in team_analyses.items():
        punt_analysis = analysis.get('punt_analysis', {})
        punt_confidence = punt_analysis.get('strategy_confidence', 'none')
        
        # Only include teams with meaningful punt strategies
        if punt_confidence in ['high', 'medium']:
            punt_cats = punt_analysis.get('punt_categories', [])
            for punt_cat in punt_cats:
                # Only include high and medium confidence punt categories
                if punt_cat.get('confidence') in ['high', 'medium']:
                    cat_short = punt_cat.get('short', 'Unknown')
                    if cat_short not in punt_summary:
                        punt_summary[cat_short] = []
                    punt_summary[cat_short].append({
                        'team_id': team_id,
                        'confidence': punt_cat.get('confidence', 'low')
                    })
    
    if punt_summary:
        # Sort by number of teams punting each category
        sorted_punts = sorted(punt_summary.items(), key=lambda x: len(x[1]), reverse=True)
        
        for category, teams in sorted_punts:
            if len(teams) >= 2:  # Only show if at least 2 teams are punting
                high_conf_teams = [t for t in teams if t['confidence'] == 'high']
                medium_conf_teams = [t for t in teams if t['confidence'] == 'medium']
                
                team_list_parts = []
                if high_conf_teams:
                    high_team_names = [f"Team {t['team_id']}" for t in high_conf_teams]
                    team_list_parts.append(f"**{', '.join(high_team_names)}**")
                if medium_conf_teams:
                    medium_team_names = [f"Team {t['team_id']}" for t in medium_conf_teams]
                    team_list_parts.append(f"{', '.join(medium_team_names)}")
                
                team_display = " • ".join(team_list_parts)
                confidence_info = ""
                if high_conf_teams and medium_conf_teams:
                    confidence_info = f" (Bold = high confidence)"
                
                st.markdown(f"**{category} Punt:** {team_display} ({len(teams)} teams){confidence_info}")
        
        if not any(len(teams) >= 2 for teams in punt_summary.values()):
            st.info("No widespread punt strategies detected - teams are pursuing balanced approaches.")
    else:
        st.info("No clear punt strategies detected across the league.")
    
    # Add some additional strategic insights
    if team_analyses:
        st.markdown("#### 📋 League Composition Analysis")
        
        # Count team outlook distribution
        outlooks = {}
        for analysis in team_analyses.values():
            outlook = analysis.get('team_projection', {}).get('outlook', 'Unknown')
            outlooks[outlook] = outlooks.get(outlook, 0) + 1
        
        if outlooks:
            outlook_display = []
            for outlook, count in sorted(outlooks.items(), key=lambda x: x[1], reverse=True):
                outlook_display.append(f"**{outlook}:** {count} teams")
            
            st.markdown(" • ".join(outlook_display))
        
        # Analyze grade distribution
        grades = {}
        for analysis in team_analyses.values():
            grade = analysis.get('team_projection', {}).get('grade', 'F')
            grade_tier = grade[0]  # A, B, C, D, F
            grades[grade_tier] = grades.get(grade_tier, 0) + 1
        
        if grades:
            total_teams = sum(grades.values())
            grade_display = []
            for grade in ['A', 'B', 'C', 'D', 'F']:
                count = grades.get(grade, 0)
                if count > 0:
                    percentage = (count / total_teams) * 100
                    grade_display.append(f"{grade}-tier: {count} ({percentage:.0f}%)")
            
            if grade_display:
                st.markdown(f"**Grade Distribution:** {' • '.join(grade_display)}")


def render_advanced_metrics_dashboard(team_analyses: Dict[int, Dict], league_insights: Dict[str, Any]):
    """Render advanced metrics dashboard."""
    
    st.markdown("### 📈 Advanced Metrics Dashboard")
    
    if not team_analyses:
        st.info("No team data available for advanced analysis.")
        return
    
    # Calculate league-wide advanced metrics
    all_ages = []
    all_games_played = []
    all_usage_rates = []
    all_true_shooting = []
    
    for analysis in team_analyses.values():
        advanced_metrics = analysis.get('advanced_metrics', {})
        roster_df = analysis.get('roster_df')
        
        if roster_df is not None and not roster_df.empty:
            if 'age' in roster_df.columns:
                all_ages.extend(roster_df['age'].dropna().tolist())
            if 'games_played' in roster_df.columns:
                all_games_played.extend(roster_df['games_played'].dropna().tolist())
            if 'usage_rate' in roster_df.columns:
                all_usage_rates.extend(roster_df['usage_rate'].dropna().tolist())
            if 'true_shooting_pct' in roster_df.columns:
                all_true_shooting.extend(roster_df['true_shooting_pct'].dropna().tolist())
    
    # League averages
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if all_ages:
            avg_age = sum(all_ages) / len(all_ages)
            st.metric("👤 League Avg Age", f"{avg_age:.1f}")
    
    with col2:
        if all_games_played:
            avg_gp = sum(all_games_played) / len(all_games_played)
            st.metric("🏥 Avg Games Played", f"{avg_gp:.0f}")
    
    with col3:
        if all_usage_rates:
            avg_usage = sum(all_usage_rates) / len(all_usage_rates)
            st.metric("🏀 Avg Usage Rate", f"{avg_usage:.1%}")
    
    with col4:
        if all_true_shooting:
            avg_ts = sum(all_true_shooting) / len(all_true_shooting)
            st.metric("🎯 Avg True Shooting", f"{avg_ts:.1%}")
    
    st.markdown("---")
    
    # Team-by-team advanced metrics
    st.markdown("#### 🔬 Team Advanced Metrics")
    
    for team_id, analysis in team_analyses.items():
        advanced_metrics = analysis.get('advanced_metrics', {})
        team_stats = analysis.get('team_stats', {})
        
        if advanced_metrics:
            is_user_team = team_stats.get('is_user_team', False)
            border_style = "border: 2px solid #FF6B35;" if is_user_team else ""
            user_badge = " 👤" if is_user_team else ""
            
            with st.expander(f"Team {team_id}{user_badge} - Advanced Metrics"):
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.markdown("**🏥 Durability**")
                    if 'avg_games_played' in advanced_metrics:
                        st.metric("Avg Games", f"{advanced_metrics['avg_games_played']:.0f}")
                    if 'durable_players' in advanced_metrics:
                        st.metric("Durable Players", advanced_metrics['durable_players'])
                    if 'injury_prone_players' in advanced_metrics:
                        st.metric("Injury Risk", advanced_metrics['injury_prone_players'])
                
                with col_b:
                    st.markdown("**👤 Demographics**")
                    if 'avg_age' in advanced_metrics:
                        st.metric("Avg Age", f"{advanced_metrics['avg_age']:.1f}")
                    if 'young_players' in advanced_metrics:
                        st.metric("Young Players (≤25)", advanced_metrics['young_players'])
                    if 'veteran_players' in advanced_metrics:
                        st.metric("Veterans (≥30)", advanced_metrics['veteran_players'])
                
                with col_c:
                    st.markdown("**🎯 Performance**")
                    if 'elite_players' in advanced_metrics:
                        st.metric("Elite Players", advanced_metrics['elite_players'])
                    if 'efficient_players' in advanced_metrics:
                        st.metric("Efficient Shooters", advanced_metrics['efficient_players'])
                    if 'z_score_consistency' in advanced_metrics:
                        st.metric("Consistency", advanced_metrics['z_score_consistency']) 