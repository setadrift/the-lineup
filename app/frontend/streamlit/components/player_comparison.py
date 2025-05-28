"""
The Lineup - Player Comparison Tool
Streamlit component for side-by-side player analysis and comparison
"""

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any, Optional, Tuple
import requests
from streamlit_extras.colored_header import colored_header


def safe_format_percentage(value, default="N/A"):
    """Safely format a percentage value, handling None/NaN cases."""
    if value is None or pd.isna(value):
        return default
    try:
        return f"{float(value):.1%}"
    except (ValueError, TypeError):
        return default


def safe_format_float(value, decimals=1, default="N/A"):
    """Safely format a float value, handling None/NaN cases."""
    if value is None or pd.isna(value):
        return default
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return default


def create_comparison_radar_chart(player1_data: Dict[str, Any], player2_data: Dict[str, Any], 
                                 player1_name: str, player2_name: str) -> go.Figure:
    """
    Create a radar chart comparing two players' z-scores.
    
    Args:
        player1_data: First player's z-score data
        player2_data: Second player's z-score data
        player1_name: First player's name
        player2_name: Second player's name
        
    Returns:
        Plotly figure object
    """
    # Define the categories for radar chart
    categories = [
        'Z-PTS', 'Z-REB', 'Z-AST', 'Z-STL', 'Z-BLK', 
        'Z-TO', 'Z-FG%', 'Z-FT%', 'Z-3PM'
    ]
    
    # Map z-score column names
    z_score_mapping = {
        'Z-PTS': 'z_points',
        'Z-REB': 'z_rebounds', 
        'Z-AST': 'z_assists',
        'Z-STL': 'z_steals',
        'Z-BLK': 'z_blocks',
        'Z-TO': 'z_turnovers',
        'Z-FG%': 'z_fg_pct',
        'Z-FT%': 'z_ft_pct',
        'Z-3PM': 'z_three_pm'
    }
    
    # Extract values for both players
    player1_values = []
    player2_values = []
    
    for category in categories:
        col_name = z_score_mapping[category]
        val1 = player1_data.get(col_name, 0)
        val2 = player2_data.get(col_name, 0)
        
        # Handle turnovers (negative is better)
        if category == 'Z-TO':
            val1 = -val1 if val1 else 0
            val2 = -val2 if val2 else 0
        
        player1_values.append(val1)
        player2_values.append(val2)
    
    # Create radar chart
    fig = go.Figure()
    
    # Add player 1
    fig.add_trace(go.Scatterpolar(
        r=player1_values,
        theta=categories,
        fill='toself',
        name=player1_name,
        line_color='#FF6B35',
        fillcolor='rgba(255, 107, 53, 0.2)'
    ))
    
    # Add player 2
    fig.add_trace(go.Scatterpolar(
        r=player2_values,
        theta=categories,
        fill='toself',
        name=player2_name,
        line_color='#2E86AB',
        fillcolor='rgba(46, 134, 171, 0.2)'
    ))
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[-3, 3],  # Typical z-score range
                tickmode='linear',
                tick0=-3,
                dtick=1
            )
        ),
        showlegend=True,
        title="Z-Score Comparison",
        height=500
    )
    
    return fig


def create_stat_comparison_chart(player1_data: Dict[str, Any], player2_data: Dict[str, Any],
                                player1_name: str, player2_name: str) -> go.Figure:
    """
    Create a bar chart comparing raw stats between two players.
    
    Args:
        player1_data: First player's stat data
        player2_data: Second player's stat data
        player1_name: First player's name
        player2_name: Second player's name
        
    Returns:
        Plotly figure object
    """
    # Define stats to compare
    stats = ['PPG', 'RPG', 'APG', 'SPG', 'BPG', 'TPG', 'FG%', 'FT%', '3PM']
    stat_mapping = {
        'PPG': 'points_per_game',
        'RPG': 'rebounds_per_game',
        'APG': 'assists_per_game', 
        'SPG': 'steals_per_game',
        'BPG': 'blocks_per_game',
        'TPG': 'turnovers_per_game',
        'FG%': 'fg_pct',
        'FT%': 'ft_pct',
        '3PM': 'three_pm'
    }
    
    player1_values = []
    player2_values = []
    
    for stat in stats:
        col_name = stat_mapping[stat]
        val1 = player1_data.get(col_name, 0) or 0
        val2 = player2_data.get(col_name, 0) or 0
        
        # Convert percentages to display format
        if stat in ['FG%', 'FT%']:
            val1 = val1 * 100 if val1 else 0
            val2 = val2 * 100 if val2 else 0
        
        player1_values.append(val1)
        player2_values.append(val2)
    
    # Create subplot
    fig = make_subplots(
        rows=1, cols=1,
        subplot_titles=["Season Averages Comparison"]
    )
    
    # Add bars for both players
    fig.add_trace(go.Bar(
        name=player1_name,
        x=stats,
        y=player1_values,
        marker_color='#FF6B35',
        opacity=0.8
    ))
    
    fig.add_trace(go.Bar(
        name=player2_name,
        x=stats,
        y=player2_values,
        marker_color='#2E86AB',
        opacity=0.8
    ))
    
    # Update layout
    fig.update_layout(
        barmode='group',
        height=400,
        showlegend=True,
        xaxis_title="Statistics",
        yaxis_title="Value"
    )
    
    return fig


def get_player_comparison_data(player_id: int, player_pool_df: pd.DataFrame, 
                              season: str, engine) -> Optional[Dict[str, Any]]:
    """
    Get comprehensive data for a player including stats and z-scores.
    
    Args:
        player_id: Player's ID
        player_pool_df: Full player pool DataFrame
        season: Current season
        engine: Database engine
        
    Returns:
        Dictionary with player data or None if not found
    """
    try:
        # Convert player_id to regular int to avoid numpy.int64 issues
        player_id = int(player_id)
        
        # Get basic player info from player pool
        player_info = player_pool_df[player_pool_df['player_id'] == player_id]
        
        if player_info.empty:
            return None
        
        player_row = player_info.iloc[0]
        
        # Get detailed stats including advanced stats from database
        stats_query = """
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
            ps.minutes_per_game,
            -- Advanced stats
            ps.age,
            ps.usage_rate,
            ps.true_shooting_pct,
            ps.player_efficiency_rating,
            ps.points_per_36,
            ps.rebounds_per_36,
            ps.assists_per_36
        FROM player_stats ps
        WHERE ps.season = %s AND ps.player_id = %s
        ORDER BY ps.player_id
        """
        
        stats_df = pd.read_sql(stats_query, engine, params=(season, player_id))
        
        # Combine data
        result = {
            'player_id': player_id,
            'name': player_row.get('name', 'Unknown'),
            'team': player_row.get('team', 'N/A'),
            'position': player_row.get('position', 'N/A'),
            'total_z_score': player_row.get('total_z_score', 0),
            'adp': player_row.get('adp', None),
            # Z-scores from player pool
            'z_points': player_row.get('z_points', 0),
            'z_rebounds': player_row.get('z_rebounds', 0),
            'z_assists': player_row.get('z_assists', 0),
            'z_steals': player_row.get('z_steals', 0),
            'z_blocks': player_row.get('z_blocks', 0),
            'z_turnovers': player_row.get('z_turnovers', 0),
            'z_fg_pct': player_row.get('z_fg_pct', 0),
            'z_ft_pct': player_row.get('z_ft_pct', 0),
            'z_three_pm': player_row.get('z_three_pm', 0)
        }
        
        # Add detailed stats if available
        if not stats_df.empty:
            stats_row = stats_df.iloc[0]
            result.update({
                # Basic stats
                'points_per_game': stats_row.get('points_per_game', 0),
                'rebounds_per_game': stats_row.get('rebounds_per_game', 0),
                'assists_per_game': stats_row.get('assists_per_game', 0),
                'steals_per_game': stats_row.get('steals_per_game', 0),
                'blocks_per_game': stats_row.get('blocks_per_game', 0),
                'turnovers_per_game': stats_row.get('turnovers_per_game', 0),
                'fg_pct': stats_row.get('fg_pct', 0),
                'ft_pct': stats_row.get('ft_pct', 0),
                'three_pm': stats_row.get('three_pm', 0),
                'games_played': stats_row.get('games_played', 0),
                'minutes_per_game': stats_row.get('minutes_per_game', 0),
                # Advanced stats
                'age': stats_row.get('age', None),
                'usage_rate': stats_row.get('usage_rate', None),
                'true_shooting_pct': stats_row.get('true_shooting_pct', None),
                'player_efficiency_rating': stats_row.get('player_efficiency_rating', None),
                'points_per_36': stats_row.get('points_per_36', None),
                'rebounds_per_36': stats_row.get('rebounds_per_36', None),
                'assists_per_36': stats_row.get('assists_per_36', None)
            })
        
        return result
        
    except Exception as e:
        # Use print instead of st.error when not in Streamlit context
        if 'streamlit' in str(type(e)) or hasattr(e, '_streamlit_error'):
            import streamlit as st
            st.error(f"Error fetching player data: {e}")
        else:
            print(f"Error fetching player data: {e}")
        return None


def get_historical_trends_comparison(player1_id: int, player2_id: int, 
                                   api_base_url: str = "http://localhost:8000") -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Get historical trends data for both players.
    
    Args:
        player1_id: First player's ID
        player2_id: Second player's ID
        api_base_url: Base URL for the API (fallback to direct DB if API unavailable)
        
    Returns:
        Tuple of (player1_trends, player2_trends)
    """
    try:
        # Try API first
        response1 = requests.get(f"{api_base_url}/api/historical/player/{player1_id}/sparklines?seasons_back=3", timeout=3)
        response2 = requests.get(f"{api_base_url}/api/historical/player/{player2_id}/sparklines?seasons_back=3", timeout=3)
        
        if response1.status_code == 200 and response2.status_code == 200:
            return response1.json(), response2.json()
        
    except:
        pass
    
    # Fallback to direct database query if API is unavailable
    try:
        from app.db.connection import get_engine
        import pandas as pd
        
        engine = get_engine()
        
        # Get last 3 seasons of data for both players
        seasons = ["2021-22", "2022-23", "2023-24"]
        
        def get_player_trends(player_id: int) -> Optional[Dict]:
            trends = {}
            
            for stat in ['points_per_game', 'rebounds_per_game', 'assists_per_game']:
                query = """
                SELECT season, {} as stat_value
                FROM player_stats 
                WHERE player_id = %s AND season = ANY(%s)
                ORDER BY season
                """.format(stat)
                
                df = pd.read_sql(query, engine, params=(player_id, seasons))
                
                if not df.empty:
                    values = df['stat_value'].tolist()
                    latest_value = values[-1] if values else 0
                    
                    # Simple trend calculation
                    if len(values) >= 2:
                        if values[-1] > values[-2] * 1.1:  # 10% increase
                            trend = 'increasing'
                        elif values[-1] < values[-2] * 0.9:  # 10% decrease
                            trend = 'decreasing'
                        else:
                            trend = 'stable'
                    else:
                        trend = 'stable'
                    
                    trends[stat] = {
                        'trend': trend,
                        'latest_value': latest_value,
                        'values': values
                    }
            
            return trends if trends else None
        
        player1_trends = get_player_trends(player1_id)
        player2_trends = get_player_trends(player2_id)
        
        return player1_trends, player2_trends
        
    except Exception as e:
        print(f"Error getting trends from database: {e}")
        return None, None


def render_player_comparison_tool(available_players_df: pd.DataFrame, player_pool_df: pd.DataFrame, 
                                 season: str, engine, api_base_url: str = "http://localhost:8000") -> None:
    """
    Render the complete player comparison tool.
    
    Args:
        available_players_df: DataFrame of available players
        player_pool_df: Full player pool DataFrame
        season: Current season
        engine: Database engine
        api_base_url: Base URL for the API
    """
    colored_header(
        label="⚖️ Player Comparison Tool",
        description="Compare two players side-by-side with stats, z-scores, and trends",
        color_name="blue-70"
    )
    
    # Player selection
    st.markdown("### 🔍 Select Players to Compare")
    
    col_player1, col_vs, col_player2 = st.columns([5, 1, 5])
    
    # Create player options
    player_options = available_players_df[['player_id', 'name', 'team', 'position']].copy()
    player_options['display'] = player_options['name'] + " (" + player_options['team'] + " - " + player_options['position'] + ")"
    
    with col_player1:
        st.markdown("#### 🏀 Player 1")
        selected_player1 = st.selectbox(
            "Choose first player:",
            options=player_options['display'].tolist(),
            key="player1_select",
            help="Select the first player for comparison"
        )
        
        if selected_player1:
            player1_idx = player_options[player_options['display'] == selected_player1].index[0]
            player1_id = player_options.loc[player1_idx, 'player_id']
            player1_name = player_options.loc[player1_idx, 'name']
    
    with col_vs:
        st.markdown("#### ")
        st.markdown("### VS")
    
    with col_player2:
        st.markdown("#### 🏀 Player 2")
        selected_player2 = st.selectbox(
            "Choose second player:",
            options=player_options['display'].tolist(),
            key="player2_select",
            help="Select the second player for comparison"
        )
        
        if selected_player2:
            player2_idx = player_options[player_options['display'] == selected_player2].index[0]
            player2_id = player_options.loc[player2_idx, 'player_id']
            player2_name = player_options.loc[player2_idx, 'name']
    
    # Only proceed if both players are selected and different
    if selected_player1 and selected_player2 and selected_player1 != selected_player2:
        
        # Get comprehensive data for both players
        with st.spinner("Loading player data..."):
            player1_data = get_player_comparison_data(player1_id, player_pool_df, season, engine)
            player2_data = get_player_comparison_data(player2_id, player_pool_df, season, engine)
        
        if not player1_data or not player2_data:
            st.error("Unable to load data for one or both players.")
            return
        
        # Display comparison
        st.markdown("---")
        
        # Basic info comparison
        st.markdown("### 📋 Player Overview")
        
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            adp_display = safe_format_float(player1_data['adp'], decimals=1) if player1_data['adp'] else 'N/A'
            st.markdown(f"""
            **{player1_data['name']}**
            - **Team:** {player1_data['team']}
            - **Position:** {player1_data['position']}
            - **Total Z-Score:** {safe_format_float(player1_data['total_z_score'], decimals=2)}
            - **ADP:** {adp_display}
            """)
        
        with col_info2:
            adp_display = safe_format_float(player2_data['adp'], decimals=1) if player2_data['adp'] else 'N/A'
            st.markdown(f"""
            **{player2_data['name']}**
            - **Team:** {player2_data['team']}
            - **Position:** {player2_data['position']}
            - **Total Z-Score:** {safe_format_float(player2_data['total_z_score'], decimals=2)}
            - **ADP:** {adp_display}
            """)
        
        # Winner indicator
        try:
            z1 = float(player1_data.get('total_z_score', 0) or 0)
            z2 = float(player2_data.get('total_z_score', 0) or 0)
            
            if z1 > z2:
                diff = safe_format_float(z1 - z2, decimals=2)
                st.success(f"🏆 **{player1_data['name']}** has a higher total Z-Score (+{diff})")
            elif z2 > z1:
                diff = safe_format_float(z2 - z1, decimals=2)
                st.success(f"🏆 **{player2_data['name']}** has a higher total Z-Score (+{diff})")
            else:
                st.info("🤝 Players have identical total Z-Scores")
        except (ValueError, TypeError):
            st.info("🤝 Unable to compare Z-Scores")
        
        # Create tabs for different views
        tab_overview, tab_radar, tab_stats, tab_zscore, tab_advanced, tab_trends, tab_summary = st.tabs([
            "📋 Overview", "📊 Radar Chart", "📈 Season Stats", "⚡ Z-Scores", "🔬 Advanced Stats", "📉 Trends", "📝 Summary"
        ])
        
        with tab_overview:
            st.markdown("### 📋 Player Overview")
            
            # Basic info comparison
            col_info1, col_info2 = st.columns(2)
            
            with col_info1:
                adp_display = safe_format_float(player1_data['adp'], decimals=1) if player1_data['adp'] else 'N/A'
                st.markdown(f"""
                **{player1_data['name']}**
                - **Team:** {player1_data['team']}
                - **Position:** {player1_data['position']}
                - **Total Z-Score:** {safe_format_float(player1_data['total_z_score'], decimals=2)}
                - **ADP:** {adp_display}
                """)
            
            with col_info2:
                adp_display = safe_format_float(player2_data['adp'], decimals=1) if player2_data['adp'] else 'N/A'
                st.markdown(f"""
                **{player2_data['name']}**
                - **Team:** {player2_data['team']}
                - **Position:** {player2_data['position']}
                - **Total Z-Score:** {safe_format_float(player2_data['total_z_score'], decimals=2)}
                - **ADP:** {adp_display}
                """)
            
            # Winner indicator
            try:
                z1 = float(player1_data.get('total_z_score', 0) or 0)
                z2 = float(player2_data.get('total_z_score', 0) or 0)
                
                if z1 > z2:
                    diff = safe_format_float(z1 - z2, decimals=2)
                    st.success(f"🏆 **{player1_data['name']}** has a higher total Z-Score (+{diff})")
                elif z2 > z1:
                    diff = safe_format_float(z2 - z1, decimals=2)
                    st.success(f"🏆 **{player2_data['name']}** has a higher total Z-Score (+{diff})")
                else:
                    st.info("🤝 Players have identical total Z-Scores")
            except (ValueError, TypeError):
                st.info("🤝 Unable to compare Z-Scores")
        
        with tab_radar:
            st.markdown("### 📊 Radar Chart")
            
            # Create radar chart
            fig_radar = create_comparison_radar_chart(
                player1_data, player2_data, player1_name, player2_name
            )
            st.plotly_chart(fig_radar, use_container_width=True, key="radar_chart_tab")
        
        with tab_stats:
            st.markdown("### 📊 Season Averages Comparison")
            
            # Create stats comparison chart
            if all(key in player1_data for key in ['points_per_game', 'rebounds_per_game']) and \
               all(key in player2_data for key in ['points_per_game', 'rebounds_per_game']):
                
                fig_stats = create_stat_comparison_chart(
                    player1_data, player2_data, player1_name, player2_name
                )
                st.plotly_chart(fig_stats, use_container_width=True, key="stats_chart_tab")
                
                # Detailed stats table
                st.markdown("#### Detailed Statistics")
                
                stats_comparison = pd.DataFrame({
                    'Statistic': ['PPG', 'RPG', 'APG', 'SPG', 'BPG', 'TPG', 'FG%', 'FT%', '3PM', 'GP', 'MPG'],
                    player1_name: [
                        safe_format_float(player1_data.get('points_per_game', 0)),
                        safe_format_float(player1_data.get('rebounds_per_game', 0)),
                        safe_format_float(player1_data.get('assists_per_game', 0)),
                        safe_format_float(player1_data.get('steals_per_game', 0)),
                        safe_format_float(player1_data.get('blocks_per_game', 0)),
                        safe_format_float(player1_data.get('turnovers_per_game', 0)),
                        safe_format_percentage(player1_data.get('fg_pct', 0)),
                        safe_format_percentage(player1_data.get('ft_pct', 0)),
                        safe_format_float(player1_data.get('three_pm', 0)),
                        safe_format_float(player1_data.get('games_played', 0), decimals=0),
                        safe_format_float(player1_data.get('minutes_per_game', 0))
                    ],
                    player2_name: [
                        safe_format_float(player2_data.get('points_per_game', 0)),
                        safe_format_float(player2_data.get('rebounds_per_game', 0)),
                        safe_format_float(player2_data.get('assists_per_game', 0)),
                        safe_format_float(player2_data.get('steals_per_game', 0)),
                        safe_format_float(player2_data.get('blocks_per_game', 0)),
                        safe_format_float(player2_data.get('turnovers_per_game', 0)),
                        safe_format_percentage(player2_data.get('fg_pct', 0)),
                        safe_format_percentage(player2_data.get('ft_pct', 0)),
                        safe_format_float(player2_data.get('three_pm', 0)),
                        safe_format_float(player2_data.get('games_played', 0), decimals=0),
                        safe_format_float(player2_data.get('minutes_per_game', 0))
                    ]
                })
                
                st.dataframe(stats_comparison, use_container_width=True, hide_index=True)
            else:
                st.warning("Detailed season stats not available for comparison.")
        
        with tab_zscore:
            st.markdown("### ⚡ Z-Score Analysis")
            
            # Create radar chart
            fig_radar = create_comparison_radar_chart(
                player1_data, player2_data, player1_name, player2_name
            )
            st.plotly_chart(fig_radar, use_container_width=True, key="zscore_radar_chart_tab")
            
            # Z-score table
            st.markdown("#### Z-Score Breakdown")
            
            zscore_comparison = pd.DataFrame({
                'Category': ['Points', 'Rebounds', 'Assists', 'Steals', 'Blocks', 'Turnovers*', 'FG%', 'FT%', '3PM'],
                player1_name: [
                    safe_format_float(player1_data.get('z_points', 0), decimals=2),
                    safe_format_float(player1_data.get('z_rebounds', 0), decimals=2),
                    safe_format_float(player1_data.get('z_assists', 0), decimals=2),
                    safe_format_float(player1_data.get('z_steals', 0), decimals=2),
                    safe_format_float(player1_data.get('z_blocks', 0), decimals=2),
                    safe_format_float(player1_data.get('z_turnovers', 0), decimals=2),
                    safe_format_float(player1_data.get('z_fg_pct', 0), decimals=2),
                    safe_format_float(player1_data.get('z_ft_pct', 0), decimals=2),
                    safe_format_float(player1_data.get('z_three_pm', 0), decimals=2)
                ],
                player2_name: [
                    safe_format_float(player2_data.get('z_points', 0), decimals=2),
                    safe_format_float(player2_data.get('z_rebounds', 0), decimals=2),
                    safe_format_float(player2_data.get('z_assists', 0), decimals=2),
                    safe_format_float(player2_data.get('z_steals', 0), decimals=2),
                    safe_format_float(player2_data.get('z_blocks', 0), decimals=2),
                    safe_format_float(player2_data.get('z_turnovers', 0), decimals=2),
                    safe_format_float(player2_data.get('z_fg_pct', 0), decimals=2),
                    safe_format_float(player2_data.get('z_ft_pct', 0), decimals=2),
                    safe_format_float(player2_data.get('z_three_pm', 0), decimals=2)
                ]
            })
            
            st.dataframe(zscore_comparison, use_container_width=True, hide_index=True)
            st.caption("*Lower turnovers are better (negative z-score is good)")
        
        with tab_advanced:
            st.markdown("### 🔬 Advanced Stats")
            
            # Check if advanced stats are available
            advanced_stats_available = any([
                'usage_rate' in player1_data, 'true_shooting_pct' in player1_data,
                'player_efficiency_rating' in player1_data, 'points_per_36' in player1_data
            ])
            
            if advanced_stats_available:
                # Efficiency Metrics
                st.markdown("#### ⚡ Efficiency Metrics")
                
                efficiency_comparison = pd.DataFrame({
                    'Metric': ['Usage Rate', 'True Shooting %', 'Player Efficiency Rating'],
                    player1_name: [
                        safe_format_percentage(player1_data.get('usage_rate', 0)),
                        safe_format_percentage(player1_data.get('true_shooting_pct', 0)),
                        safe_format_float(player1_data.get('player_efficiency_rating', 0))
                    ],
                    player2_name: [
                        safe_format_percentage(player2_data.get('usage_rate', 0)),
                        safe_format_percentage(player2_data.get('true_shooting_pct', 0)),
                        safe_format_float(player2_data.get('player_efficiency_rating', 0))
                    ]
                })
                
                st.dataframe(efficiency_comparison, use_container_width=True, hide_index=True)
                
                # Per-36 Stats
                if 'points_per_36' in player1_data or 'points_per_36' in player2_data:
                    st.markdown("#### 📊 Per-36 Minute Stats")
                    
                    per36_comparison = pd.DataFrame({
                        'Stat': ['Points/36', 'Rebounds/36', 'Assists/36'],
                        player1_name: [
                            safe_format_float(player1_data.get('points_per_36', 0)),
                            safe_format_float(player1_data.get('rebounds_per_36', 0)),
                            safe_format_float(player1_data.get('assists_per_36', 0))
                        ],
                        player2_name: [
                            safe_format_float(player2_data.get('points_per_36', 0)),
                            safe_format_float(player2_data.get('rebounds_per_36', 0)),
                            safe_format_float(player2_data.get('assists_per_36', 0))
                        ]
                    })
                    
                    st.dataframe(per36_comparison, use_container_width=True, hide_index=True)
                
                # Age and Durability
                st.markdown("#### 🏃 Age & Durability")
                
                durability_comparison = pd.DataFrame({
                    'Factor': ['Age', 'Games Played', 'Minutes/Game'],
                    player1_name: [
                        safe_format_float(player1_data.get('age', 0), decimals=0),
                        safe_format_float(player1_data.get('games_played', 0), decimals=0),
                        safe_format_float(player1_data.get('minutes_per_game', 0))
                    ],
                    player2_name: [
                        safe_format_float(player2_data.get('age', 0), decimals=0),
                        safe_format_float(player2_data.get('games_played', 0), decimals=0),
                        safe_format_float(player2_data.get('minutes_per_game', 0))
                    ]
                })
                
                st.dataframe(durability_comparison, use_container_width=True, hide_index=True)
                
                # Advanced insights
                st.markdown("#### 💡 Advanced Insights")
                
                insights = []
                
                # Usage rate comparison
                try:
                    usage1 = float(player1_data.get('usage_rate', 0) or 0)
                    usage2 = float(player2_data.get('usage_rate', 0) or 0)
                    
                    if usage1 > 0.28 or usage2 > 0.28:
                        high_usage_player = player1_name if usage1 > usage2 else player2_name
                        insights.append(f"🎯 **{high_usage_player}** has higher usage rate - more involved in offense")
                except (ValueError, TypeError):
                    pass
                
                # Efficiency comparison
                try:
                    ts1 = float(player1_data.get('true_shooting_pct', 0) or 0)
                    ts2 = float(player2_data.get('true_shooting_pct', 0) or 0)
                    
                    if abs(ts1 - ts2) > 0.05:  # 5% difference
                        efficient_player = player1_name if ts1 > ts2 else player2_name
                        insights.append(f"🎯 **{efficient_player}** is significantly more efficient shooter")
                except (ValueError, TypeError):
                    pass
                
                # Age comparison
                try:
                    age1 = float(player1_data.get('age', 0) or 0)
                    age2 = float(player2_data.get('age', 0) or 0)
                    
                    if abs(age1 - age2) >= 3:  # 3+ year difference
                        younger_player = player1_name if age1 < age2 else player2_name
                        insights.append(f"🌟 **{younger_player}** is significantly younger - more upside potential")
                except (ValueError, TypeError):
                    pass
                
                # Games played comparison
                try:
                    gp1 = float(player1_data.get('games_played', 0) or 0)
                    gp2 = float(player2_data.get('games_played', 0) or 0)
                    
                    if gp1 >= 70 and gp2 < 60:
                        insights.append(f"💪 **{player1_name}** has better durability (70+ games)")
                    elif gp2 >= 70 and gp1 < 60:
                        insights.append(f"💪 **{player2_name}** has better durability (70+ games)")
                except (ValueError, TypeError):
                    pass
                
                if insights:
                    for insight in insights:
                        st.markdown(insight)
                else:
                    st.info("Players have similar advanced metrics")
                
                # Explanations - using markdown instead of expander to avoid nesting
                st.markdown("---")
                st.markdown("#### 📚 Advanced Stats Explained")
                st.markdown("""
                **Usage Rate**: Percentage of team plays used by player while on court
                - Elite: 28%+, Good: 25-28%, Average: 20-25%
                
                **True Shooting %**: Shooting efficiency accounting for 3-pointers and free throws
                - Elite: 60%+, Good: 55-60%, Average: 52-55%
                
                **Player Efficiency Rating (PER)**: Overall efficiency metric
                - Elite: 25+, Very Good: 20-25, Average: 15, Below Average: <15
                
                **Per-36 Stats**: Statistics projected to 36 minutes of play
                - Useful for comparing players with different playing time
                """)
            else:
                st.info("Advanced stats not available for these players. Run the advanced feature generation to see these metrics.")
        
        with tab_trends:
            st.markdown("### 📈 Historical Trends Comparison")
            
            # Get historical trends
            with st.spinner("Loading historical trends..."):
                player1_trends, player2_trends = get_historical_trends_comparison(
                    player1_id, player2_id, api_base_url
                )
            
            if player1_trends and player2_trends:
                # Compare key trends
                key_stats = ['points_per_game', 'rebounds_per_game', 'assists_per_game']
                
                col_trend1, col_trend2 = st.columns(2)
                
                with col_trend1:
                    st.markdown(f"#### {player1_name} Trends")
                    for stat in key_stats:
                        if stat in player1_trends:
                            trend_data = player1_trends[stat]
                            trend = trend_data.get('trend', 'stable')
                            latest = trend_data.get('latest_value', 0)
                            
                            trend_emoji = {'increasing': '📈', 'decreasing': '📉', 'stable': '➡️', 'volatile': '📊'}.get(trend, '📊')
                            stat_display = stat.replace('_per_game', '').replace('_', ' ').title()
                            
                            st.markdown(f"**{trend_emoji} {stat_display}:** {latest:.1f} ({trend})")
                
                with col_trend2:
                    st.markdown(f"#### {player2_name} Trends")
                    for stat in key_stats:
                        if stat in player2_trends:
                            trend_data = player2_trends[stat]
                            trend = trend_data.get('trend', 'stable')
                            latest = trend_data.get('latest_value', 0)
                            
                            trend_emoji = {'increasing': '📈', 'decreasing': '📉', 'stable': '➡️', 'volatile': '📊'}.get(trend, '📊')
                            stat_display = stat.replace('_per_game', '').replace('_', ' ').title()
                            
                            st.markdown(f"**{trend_emoji} {stat_display}:** {latest:.1f} ({trend})")
                
                # Trend summary
                st.markdown("#### Trend Analysis")
                
                # Count improving trends for each player
                p1_improving = sum(1 for stat in key_stats if player1_trends.get(stat, {}).get('trend') == 'increasing')
                p2_improving = sum(1 for stat in key_stats if player2_trends.get(stat, {}).get('trend') == 'increasing')
                
                if p1_improving > p2_improving:
                    st.success(f"📈 **{player1_name}** has more improving trends ({p1_improving} vs {p2_improving})")
                elif p2_improving > p1_improving:
                    st.success(f"📈 **{player2_name}** has more improving trends ({p2_improving} vs {p1_improving})")
                else:
                    st.info("🤝 Both players have similar trend patterns")
            else:
                st.info("Historical trends data not available for comparison")
        
        with tab_summary:
            st.markdown("### 📝 Comparison Summary")
            
            # Generate comparison insights
            insights = []
            
            # Z-score comparison
            z_diff = player1_data['total_z_score'] - player2_data['total_z_score']
            if abs(z_diff) > 1.0:
                winner = player1_name if z_diff > 0 else player2_name
                insights.append(f"🏆 **Overall Value**: {winner} has significantly higher fantasy value")
            else:
                insights.append("🤝 **Overall Value**: Players have similar fantasy value")
            
            # Position comparison
            if player1_data['position'] == player2_data['position']:
                insights.append(f"⚖️ **Position**: Both play {player1_data['position']} - direct positional comparison")
            else:
                insights.append(f"🔄 **Position**: Different positions ({player1_data['position']} vs {player2_data['position']}) - consider positional needs")
            
            # ADP comparison
            if player1_data['adp'] and player2_data['adp']:
                adp_diff = player1_data['adp'] - player2_data['adp']
                if abs(adp_diff) > 10:
                    earlier_pick = player1_name if adp_diff < 0 else player2_name
                    insights.append(f"📊 **Draft Position**: {earlier_pick} typically drafted significantly earlier")
                else:
                    insights.append("📊 **Draft Position**: Similar ADP - comparable draft value")
            
            # Category strengths
            p1_strengths = []
            p2_strengths = []
            
            categories = ['z_points', 'z_rebounds', 'z_assists', 'z_steals', 'z_blocks', 'z_fg_pct', 'z_ft_pct', 'z_three_pm']
            cat_names = ['Points', 'Rebounds', 'Assists', 'Steals', 'Blocks', 'FG%', 'FT%', '3PM']
            
            for i, cat in enumerate(categories):
                p1_val = player1_data.get(cat, 0)
                p2_val = player2_data.get(cat, 0)
                
                if p1_val > p2_val + 0.5:
                    p1_strengths.append(cat_names[i])
                elif p2_val > p1_val + 0.5:
                    p2_strengths.append(cat_names[i])
            
            if p1_strengths:
                insights.append(f"💪 **{player1_name} Strengths**: {', '.join(p1_strengths)}")
            
            if p2_strengths:
                insights.append(f"💪 **{player2_name} Strengths**: {', '.join(p2_strengths)}")
            
            # Display insights
            for insight in insights:
                st.markdown(f"- {insight}")
            
            # Recommendation
            st.markdown("---")
            st.markdown("#### 🎯 Draft Recommendation")
            
            if abs(z_diff) > 1.0:
                winner = player1_name if z_diff > 0 else player2_name
                st.success(f"**Recommendation**: Draft **{winner}** - significantly higher fantasy value")
            else:
                st.info("**Recommendation**: Both players offer similar value - consider team needs and positional requirements")
    
    elif selected_player1 and selected_player2 and selected_player1 == selected_player2:
        st.warning("⚠️ Please select two different players to compare.")
    else:
        st.info("👆 Select two players above to begin comparison.") 