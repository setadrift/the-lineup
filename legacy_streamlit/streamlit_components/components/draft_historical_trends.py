"""
The Lineup - Draft Historical Trends Integration
Streamlit component for displaying historical trends within the draft assistant
"""

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional
import requests
from streamlit_extras.colored_header import colored_header


def create_compact_sparkline(values: List[float], seasons: List[str], stat_name: str, 
                           trend: str = 'stable', width: int = 150, height: int = 40) -> go.Figure:
    """
    Create a compact sparkline for the draft assistant.
    
    Args:
        values: List of stat values across seasons
        seasons: List of season labels
        stat_name: Name of the stat for labeling
        trend: Trend direction
        width: Chart width in pixels
        height: Chart height in pixels
        
    Returns:
        Plotly figure object
    """
    if not values or len(values) < 2:
        # Create empty sparkline
        fig = go.Figure()
        fig.add_annotation(
            text="No data",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=8, color="gray")
        )
        fig.update_layout(
            width=width, height=height,
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        return fig
    
    # Color mapping for trends
    trend_colors = {
        'increasing': '#28a745',
        'decreasing': '#dc3545',
        'stable': '#6c757d',
        'volatile': '#fd7e14'
    }
    
    color = trend_colors.get(trend, '#6c757d')
    
    # Create the sparkline
    fig = go.Figure()
    
    # Add the line
    fig.add_trace(go.Scatter(
        x=list(range(len(values))),
        y=values,
        mode='lines+markers',
        line=dict(color=color, width=1.5),
        marker=dict(size=3, color=color),
        hovertemplate=f'<b>{stat_name}</b><br>' +
                     'Season: %{customdata}<br>' +
                     'Value: %{y:.1f}<extra></extra>',
        customdata=seasons,
        showlegend=False
    ))
    
    # Update layout for compact sparkline
    fig.update_layout(
        width=width,
        height=height,
        margin=dict(l=2, r=2, t=2, b=2),
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='closest'
    )
    
    return fig


def render_player_trend_summary(player_id: int, player_name: str, 
                               api_base_url: str = "http://localhost:8000") -> Optional[Dict[str, Any]]:
    """
    Render a compact trend summary for a player in the draft context.
    
    Args:
        player_id: The player's ID
        player_name: Player's name
        api_base_url: Base URL for the API
        
    Returns:
        Trend data if successful, None otherwise
    """
    try:
        response = requests.get(f"{api_base_url}/api/historical/player/{player_id}/trends?seasons_back=3", timeout=3)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        sparklines = data.get('sparklines', {})
        seasons_analyzed = data.get('seasons_analyzed', 0)
        
        if seasons_analyzed == 0:
            return None
        
        # Count trends for quick assessment
        trend_counts = {'increasing': 0, 'decreasing': 0, 'stable': 0, 'volatile': 0}
        key_stats = ['points_per_game', 'rebounds_per_game', 'assists_per_game', 'steals_per_game', 'blocks_per_game']
        
        for stat in key_stats:
            if stat in sparklines:
                trend = sparklines[stat].get('trend', 'stable')
                if trend in trend_counts:
                    trend_counts[trend] += 1
        
        return {
            'sparklines': sparklines,
            'trend_counts': trend_counts,
            'seasons_analyzed': seasons_analyzed,
            'overall_trend': 'improving' if trend_counts['increasing'] > trend_counts['decreasing'] else 
                           'declining' if trend_counts['decreasing'] > trend_counts['increasing'] else 'mixed'
        }
    
    except:
        return None


def render_draft_historical_trends_tab(available_players_df: pd.DataFrame, 
                                     api_base_url: str = "http://localhost:8000") -> None:
    """
    Render the historical trends tab within the draft assistant.
    
    Args:
        available_players_df: DataFrame of available players
        api_base_url: Base URL for the API
    """
    st.markdown("### 📈 Historical Trends Analysis")
    st.markdown("*Analyze player performance trends over the last 3 seasons*")
    
    # Player selection
    col_select, col_info = st.columns([2, 1])
    
    with col_select:
        # Create a searchable selectbox
        player_options = available_players_df[['player_id', 'name']].copy()
        player_options['display'] = player_options['name'] + f" (ID: " + player_options['player_id'].astype(str) + ")"
        
        selected_player = st.selectbox(
            "🔍 Select a player to analyze:",
            options=player_options['display'].tolist(),
            help="Choose a player and click 'Analyze Trends' to view their historical performance"
        )
        
        # Add confirmation button
        analyze_clicked = st.button("📈 Analyze Trends", key="analyze_trends", type="primary")
        
        if selected_player and analyze_clicked:
            # Extract player info
            selected_idx = player_options[player_options['display'] == selected_player].index[0]
            player_id = player_options.loc[selected_idx, 'player_id']
            player_name = player_options.loc[selected_idx, 'name']
            
            # Get player info from the available players df
            player_info = available_players_df[available_players_df['player_id'] == player_id].iloc[0]
            
            # Store in session state to persist the analysis
            st.session_state.trends_player_id = player_id
            st.session_state.trends_player_name = player_name
            st.session_state.trends_player_info = player_info
    
    with col_info:
        if selected_player:
            # Show basic info even before analysis
            selected_idx = player_options[player_options['display'] == selected_player].index[0]
            player_info = available_players_df[available_players_df['player_id'] == player_options.loc[selected_idx, 'player_id']].iloc[0]
            
            st.markdown("**Player Info:**")
            st.markdown(f"**Team:** {player_info.get('team', 'N/A')}")
            st.markdown(f"**Position:** {player_info.get('position', 'N/A')}")
            st.markdown(f"**Z-Score:** {player_info.get('total_z_score', 0):.2f}")
            st.markdown(f"**ADP:** {player_info.get('adp', 'N/A')}")
    
    # Show analysis if player has been confirmed
    if (hasattr(st.session_state, 'trends_player_id') and 
        hasattr(st.session_state, 'trends_player_name') and 
        hasattr(st.session_state, 'trends_player_info')):
        
        player_id = st.session_state.trends_player_id
        player_name = st.session_state.trends_player_name
        player_info = st.session_state.trends_player_info
        
        st.markdown("---")
        st.markdown(f"### 📊 Trends Analysis for {player_name}")
        
        with st.spinner("Loading historical trends..."):
            trend_data = render_player_trend_summary(player_id, player_name, api_base_url)
            
            if trend_data:
                sparklines = trend_data['sparklines']
                trend_counts = trend_data['trend_counts']
                seasons_analyzed = trend_data['seasons_analyzed']
                overall_trend = trend_data['overall_trend']
                
                # Overall trend indicator
                col_trend1, col_trend2, col_trend3 = st.columns(3)
                
                with col_trend1:
                    if overall_trend == 'improving':
                        st.success(f"📈 **Overall Trend: Improving**")
                    elif overall_trend == 'declining':
                        st.warning(f"📉 **Overall Trend: Declining**")
                    else:
                        st.info(f"📊 **Overall Trend: Mixed**")
                
                with col_trend2:
                    st.metric("Seasons Analyzed", seasons_analyzed)
                
                with col_trend3:
                    improving_stats = trend_counts['increasing']
                    st.metric("📈 Improving Stats", improving_stats)
                
                # Key stats sparklines
                st.markdown("---")
                st.markdown("#### 🏀 Key Performance Trends")
                
                # Organize stats in a grid
                stat_names = {
                    'points_per_game': 'Points',
                    'rebounds_per_game': 'Rebounds', 
                    'assists_per_game': 'Assists',
                    'steals_per_game': 'Steals',
                    'blocks_per_game': 'Blocks'
                }
                
                # Create 3 columns for sparklines
                cols = st.columns(3)
                
                for i, (stat_key, stat_display) in enumerate(stat_names.items()):
                    if stat_key in sparklines:
                        sparkline_data = sparklines[stat_key]
                        values = sparkline_data.get('values', [])
                        seasons = sparkline_data.get('seasons', [])
                        trend = sparkline_data.get('trend', 'stable')
                        latest_value = sparkline_data.get('latest_value')
                        change_from_previous = sparkline_data.get('change_from_previous')
                        
                        with cols[i % 3]:
                            # Trend emoji
                            trend_emojis = {
                                'increasing': '📈',
                                'decreasing': '📉', 
                                'stable': '➡️',
                                'volatile': '📊'
                            }
                            
                            st.markdown(f"**{trend_emojis.get(trend, '📊')} {stat_display}**")
                            
                            if values:
                                # Create compact sparkline
                                fig = create_compact_sparkline(values, seasons, stat_display, trend)
                                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                                
                                # Show current value and change
                                if latest_value is not None:
                                    delta_str = f"{change_from_previous:+.1f}" if change_from_previous is not None else None
                                    st.metric("", f"{latest_value:.1f}", delta=delta_str)
                            else:
                                st.markdown("*No data*")
                
                # Efficiency stats
                st.markdown("---")
                st.markdown("#### 🎯 Shooting Efficiency Trends")
                
                efficiency_stats = {
                    'fg_pct': 'FG%',
                    'ft_pct': 'FT%',
                    'three_pm': '3PM'
                }
                
                eff_cols = st.columns(3)
                
                for i, (stat_key, stat_display) in enumerate(efficiency_stats.items()):
                    if stat_key in sparklines:
                        sparkline_data = sparklines[stat_key]
                        values = sparkline_data.get('values', [])
                        seasons = sparkline_data.get('seasons', [])
                        trend = sparkline_data.get('trend', 'stable')
                        latest_value = sparkline_data.get('latest_value')
                        change_from_previous = sparkline_data.get('change_from_previous')
                        
                        with eff_cols[i]:
                            trend_emojis = {
                                'increasing': '📈',
                                'decreasing': '📉',
                                'stable': '➡️', 
                                'volatile': '📊'
                            }
                            
                            st.markdown(f"**{trend_emojis.get(trend, '📊')} {stat_display}**")
                            
                            if values:
                                fig = create_compact_sparkline(values, seasons, stat_display, trend)
                                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                                
                                if latest_value is not None:
                                    if stat_key in ['fg_pct', 'ft_pct']:
                                        # Show as percentage
                                        st.metric("", f"{latest_value:.1%}")
                                    else:
                                        delta_str = f"{change_from_previous:+.1f}" if change_from_previous is not None else None
                                        st.metric("", f"{latest_value:.1f}", delta=delta_str)
                            else:
                                st.markdown("*No data*")
                
                # Draft insights
                st.markdown("---")
                st.markdown("#### 💡 Draft Insights")
                
                insights = []
                
                # Generate insights based on trends
                if trend_counts['increasing'] >= 3:
                    insights.append("🔥 **Rising Star**: Multiple stats trending upward - could be a breakout candidate")
                elif trend_counts['decreasing'] >= 3:
                    insights.append("⚠️ **Declining Performance**: Multiple stats trending downward - consider carefully")
                
                if trend_counts['volatile'] >= 2:
                    insights.append("📊 **High Volatility**: Inconsistent performance - higher risk/reward player")
                
                if trend_counts['stable'] >= 3:
                    insights.append("🎯 **Consistent Performer**: Stable production - reliable floor")
                
                # Age-based insights (if we had age data)
                if sparklines.get('points_per_game', {}).get('trend') == 'increasing':
                    insights.append("📈 **Scoring Uptrend**: Points per game improving - offensive development")
                
                if not insights:
                    insights.append("📊 **Mixed Trends**: Performance varies by category - analyze specific needs")
                
                for insight in insights:
                    st.markdown(f"- {insight}")
                
            else:
                st.info(f"📊 No historical trend data available for {player_name}")
                st.markdown("*This could mean:*")
                st.markdown("- Player is a rookie or has limited NBA history")
                st.markdown("- Data not yet loaded for this player")
                st.markdown("- Player was not active in recent seasons")


def render_quick_trend_indicators(player_ids: List[int], api_base_url: str = "http://localhost:8000") -> Dict[int, str]:
    """
    Get quick trend indicators for multiple players (for table display).
    
    Args:
        player_ids: List of player IDs
        api_base_url: Base URL for the API
        
    Returns:
        Dictionary mapping player_id to trend indicator emoji
    """
    trend_indicators = {}
    
    for player_id in player_ids[:10]:  # Limit to top 10 to avoid too many API calls
        try:
            response = requests.get(f"{api_base_url}/api/historical/player/{player_id}/sparklines?seasons_back=3", timeout=1)
            
            if response.status_code == 200:
                data = response.json()
                
                # Count trends
                trend_counts = {'increasing': 0, 'decreasing': 0}
                key_stats = ['points_per_game', 'rebounds_per_game', 'assists_per_game']
                
                for stat in key_stats:
                    if stat in data:
                        trend = data[stat].get('trend', 'stable')
                        if trend in trend_counts:
                            trend_counts[trend] += 1
                
                # Assign indicator
                if trend_counts['increasing'] > trend_counts['decreasing']:
                    trend_indicators[player_id] = "📈"
                elif trend_counts['decreasing'] > trend_counts['increasing']:
                    trend_indicators[player_id] = "📉"
                else:
                    trend_indicators[player_id] = "➡️"
            else:
                trend_indicators[player_id] = "❓"
                
        except:
            trend_indicators[player_id] = "❓"
    
    return trend_indicators 