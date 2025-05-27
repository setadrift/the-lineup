"""
The Lineup - Historical Trends Components
Streamlit components for displaying player historical stat trends and sparklines
"""

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any, Optional
import requests
from streamlit_extras.colored_header import colored_header


def create_mini_sparkline(values: List[float], seasons: List[str], stat_name: str, 
                         trend: str = 'stable', width: int = 200, height: int = 60) -> go.Figure:
    """
    Create a mini sparkline chart for a stat.
    
    Args:
        values: List of stat values across seasons
        seasons: List of season labels
        stat_name: Name of the stat for labeling
        trend: Trend direction ('increasing', 'decreasing', 'stable', 'volatile')
        width: Chart width in pixels
        height: Chart height in pixels
        
    Returns:
        Plotly figure object
    """
    if not values or len(values) < 2:
        # Create empty sparkline for no data
        fig = go.Figure()
        fig.add_annotation(
            text="No data",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=10, color="gray")
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
        'increasing': '#28a745',  # Green
        'decreasing': '#dc3545',  # Red
        'stable': '#6c757d',      # Gray
        'volatile': '#fd7e14'     # Orange
    }
    
    color = trend_colors.get(trend, '#6c757d')
    
    # Create the sparkline
    fig = go.Figure()
    
    # Add the line
    fig.add_trace(go.Scatter(
        x=list(range(len(values))),
        y=values,
        mode='lines+markers',
        line=dict(color=color, width=2),
        marker=dict(size=4, color=color),
        hovertemplate=f'<b>{stat_name}</b><br>' +
                     'Season: %{customdata}<br>' +
                     'Value: %{y:.2f}<extra></extra>',
        customdata=seasons,
        showlegend=False
    ))
    
    # Add trend arrow/indicator
    if len(values) >= 2:
        start_y = values[0]
        end_y = values[-1]
        
        # Add subtle trend line
        fig.add_trace(go.Scatter(
            x=[0, len(values)-1],
            y=[start_y, end_y],
            mode='lines',
            line=dict(color=color, width=1, dash='dot'),
            opacity=0.5,
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # Update layout for mini sparkline
    fig.update_layout(
        width=width,
        height=height,
        margin=dict(l=5, r=5, t=5, b=5),
        showlegend=False,
        xaxis=dict(
            visible=False,
            range=[-0.1, len(values)-0.9]
        ),
        yaxis=dict(
            visible=False,
            range=[min(values) * 0.95, max(values) * 1.05] if values else [0, 1]
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified'
    )
    
    return fig


def render_stat_sparkline_card(sparkline_data: Dict[str, Any], stat_display_name: str) -> None:
    """
    Render a single stat sparkline card.
    
    Args:
        sparkline_data: Dictionary containing sparkline data
        stat_display_name: Human-readable stat name
    """
    values = sparkline_data.get('values', [])
    seasons = sparkline_data.get('seasons', [])
    trend = sparkline_data.get('trend', 'stable')
    latest_value = sparkline_data.get('latest_value')
    change_from_previous = sparkline_data.get('change_from_previous')
    percent_change = sparkline_data.get('percent_change')
    
    # Create the sparkline
    fig = create_mini_sparkline(values, seasons, stat_display_name, trend)
    
    # Trend emoji mapping
    trend_emojis = {
        'increasing': '📈',
        'decreasing': '📉',
        'stable': '➡️',
        'volatile': '📊'
    }
    
    # Color mapping for change indicators
    change_color = 'normal'
    if change_from_previous is not None:
        if change_from_previous > 0:
            change_color = 'normal'  # Green in streamlit
        elif change_from_previous < 0:
            change_color = 'inverse'  # Red in streamlit
    
    # Create the card layout
    col_chart, col_info = st.columns([2, 1])
    
    with col_chart:
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with col_info:
        # Current value
        if latest_value is not None:
            st.metric(
                label=f"{trend_emojis.get(trend, '📊')} {stat_display_name}",
                value=f"{latest_value:.1f}" if isinstance(latest_value, float) else str(latest_value),
                delta=f"{change_from_previous:+.1f}" if change_from_previous is not None else None
            )
        else:
            st.markdown(f"**{trend_emojis.get(trend, '📊')} {stat_display_name}**")
            st.markdown("*No data*")
        
        # Show percent change if available
        if percent_change is not None:
            st.caption(f"({percent_change:+.1f}% vs last season)")


def render_player_historical_trends(player_id: int, player_name: str, 
                                   api_base_url: str = "http://localhost:8000",
                                   seasons_back: int = 3) -> None:
    """
    Render complete historical trends section for a player.
    
    Args:
        player_id: The player's ID
        player_name: Player's name for display
        api_base_url: Base URL for the API
        seasons_back: Number of seasons to analyze
    """
    try:
        # Fetch player trends data
        response = requests.get(f"{api_base_url}/api/historical/player/{player_id}/trends?seasons_back={seasons_back}")
        
        if response.status_code == 404:
            st.warning(f"No historical data found for {player_name}")
            return
        elif response.status_code != 200:
            st.error(f"Error fetching historical data: {response.status_code}")
            return
        
        data = response.json()
        sparklines = data.get('sparklines', {})
        historical_stats = data.get('historical_stats', [])
        seasons_analyzed = data.get('seasons_analyzed', 0)
        
        if seasons_analyzed == 0:
            st.info(f"No historical data available for {player_name}")
            return
        
        # Header
        colored_header(
            label=f"📈 Historical Trends - {player_name}",
            description=f"Last {seasons_analyzed} seasons of performance data",
            color_name="blue-70"
        )
        
        # Stat display names mapping
        stat_names = {
            'points_per_game': 'Points',
            'rebounds_per_game': 'Rebounds',
            'assists_per_game': 'Assists',
            'steals_per_game': 'Steals',
            'blocks_per_game': 'Blocks',
            'turnovers_per_game': 'Turnovers',
            'fg_pct': 'FG%',
            'ft_pct': 'FT%',
            'three_pm': '3PM'
        }
        
        # Create tabs for different categories
        tab_offense, tab_defense, tab_efficiency = st.tabs(["🏀 Offense", "🛡️ Defense", "📊 Efficiency"])
        
        with tab_offense:
            st.markdown("### Offensive Statistics")
            
            # Offensive stats in a grid
            offensive_stats = ['points_per_game', 'rebounds_per_game', 'assists_per_game', 'three_pm']
            
            cols = st.columns(2)
            for i, stat in enumerate(offensive_stats):
                if stat in sparklines:
                    with cols[i % 2]:
                        with st.container():
                            render_stat_sparkline_card(sparklines[stat], stat_names.get(stat, stat))
        
        with tab_defense:
            st.markdown("### Defensive Statistics")
            
            # Defensive stats
            defensive_stats = ['steals_per_game', 'blocks_per_game', 'turnovers_per_game']
            
            cols = st.columns(2)
            for i, stat in enumerate(defensive_stats):
                if stat in sparklines:
                    with cols[i % 2]:
                        with st.container():
                            render_stat_sparkline_card(sparklines[stat], stat_names.get(stat, stat))
        
        with tab_efficiency:
            st.markdown("### Shooting Efficiency")
            
            # Efficiency stats
            efficiency_stats = ['fg_pct', 'ft_pct']
            
            cols = st.columns(2)
            for i, stat in enumerate(efficiency_stats):
                if stat in sparklines:
                    with cols[i % 2]:
                        with st.container():
                            render_stat_sparkline_card(sparklines[stat], stat_names.get(stat, stat))
        
        # Historical data table
        if historical_stats:
            st.markdown("---")
            st.markdown("### 📋 Season-by-Season Breakdown")
            
            # Convert to DataFrame for better display
            df_historical = pd.DataFrame(historical_stats)
            
            # Select key columns for display
            display_columns = ['season', 'team', 'games_played', 'points_per_game', 
                             'rebounds_per_game', 'assists_per_game', 'fg_pct', 'ft_pct']
            
            if all(col in df_historical.columns for col in display_columns):
                df_display = df_historical[display_columns].copy()
                
                # Format the data for better display
                df_display['fg_pct'] = df_display['fg_pct'].apply(lambda x: f"{x:.1%}" if pd.notnull(x) else "N/A")
                df_display['ft_pct'] = df_display['ft_pct'].apply(lambda x: f"{x:.1%}" if pd.notnull(x) else "N/A")
                
                # Rename columns for display
                df_display.columns = ['Season', 'Team', 'GP', 'PPG', 'RPG', 'APG', 'FG%', 'FT%']
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    except requests.exceptions.ConnectionError:
        st.error("Unable to connect to the API. Please ensure the backend server is running.")
    except Exception as e:
        st.error(f"Error loading historical trends: {str(e)}")


def render_trend_summary_widget(sparklines: Dict[str, Dict[str, Any]]) -> None:
    """
    Render a compact trend summary widget showing overall player trajectory.
    
    Args:
        sparklines: Dictionary of sparkline data for all stats
    """
    if not sparklines:
        return
    
    # Count trends
    trend_counts = {'increasing': 0, 'decreasing': 0, 'stable': 0, 'volatile': 0}
    
    for stat_data in sparklines.values():
        trend = stat_data.get('trend', 'stable')
        if trend in trend_counts:
            trend_counts[trend] += 1
    
    total_stats = sum(trend_counts.values())
    
    if total_stats == 0:
        return
    
    # Create summary
    st.markdown("### 📊 Trend Summary")
    
    cols = st.columns(4)
    
    with cols[0]:
        st.metric("📈 Improving", trend_counts['increasing'])
    
    with cols[1]:
        st.metric("📉 Declining", trend_counts['decreasing'])
    
    with cols[2]:
        st.metric("➡️ Stable", trend_counts['stable'])
    
    with cols[3]:
        st.metric("📊 Volatile", trend_counts['volatile'])
    
    # Overall assessment
    if trend_counts['increasing'] > trend_counts['decreasing']:
        st.success("🔥 Overall trajectory: **Improving**")
    elif trend_counts['decreasing'] > trend_counts['increasing']:
        st.warning("⚠️ Overall trajectory: **Declining**")
    else:
        st.info("📊 Overall trajectory: **Mixed/Stable**") 