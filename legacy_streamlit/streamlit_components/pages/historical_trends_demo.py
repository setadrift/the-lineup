"""
The Lineup - Historical Trends Demo
Demo page showcasing the historical stat trends and sparklines feature
"""

import streamlit as st
import pandas as pd
import requests
from typing import Dict, Any

from legacy_streamlit.streamlit_components.components.historical_trends import (
    render_player_historical_trends,
    render_trend_summary_widget
)
from legacy_streamlit.streamlit_components.components.ui_components import render_header

# Page configuration
st.set_page_config(
    page_title="Historical Trends Demo - The Lineup",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main demo page function."""
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    
    .trend-up {
        color: #28a745;
    }
    
    .trend-down {
        color: #dc3545;
    }
    
    .trend-stable {
        color: #6c757d;
    }
    
    .trend-volatile {
        color: #fd7e14;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    render_header()
    
    st.markdown("---")
    
    # Demo introduction
    st.markdown("""
    ## 📈 Historical Stat Trends Demo
    
    This demo showcases the new **Historical Stat Trends** feature, which provides:
    
    - 📊 **Mini-sparklines** for key fantasy basketball stats
    - 📈 **Trend analysis** (increasing, decreasing, stable, volatile)
    - 🔍 **Multi-season comparisons** (last 3 seasons by default)
    - 📋 **Season-by-season breakdowns**
    
    ### How it works:
    1. **Data Analysis**: We analyze player stats across multiple seasons
    2. **Trend Calculation**: Using linear regression to determine stat trajectories
    3. **Visual Representation**: Mini-sparklines show trends at a glance
    4. **Smart Categorization**: Stats are grouped by offense, defense, and efficiency
    """)
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("### 🎛️ Demo Configuration")
        
        # API configuration
        api_base_url = st.text_input(
            "API Base URL",
            value="http://localhost:8000",
            help="Base URL for The Lineup API"
        )
        
        # Seasons back selector
        seasons_back = st.slider(
            "Seasons to Analyze",
            min_value=1,
            max_value=5,
            value=3,
            help="Number of previous seasons to include in analysis"
        )
        
        st.markdown("---")
        
        # Sample player IDs (these would come from your database)
        st.markdown("### 🏀 Sample Players")
        st.markdown("""
        Try these sample player IDs:
        - **LeBron James**: 2544
        - **Stephen Curry**: 201939
        - **Giannis Antetokounmpo**: 203507
        - **Kevin Durant**: 201142
        - **Luka Dončić**: 1629029
        
        *Note: These are NBA.com player IDs. Actual IDs in your database may differ.*
        """)
    
    # Main content area
    col_main, col_info = st.columns([3, 1])
    
    with col_main:
        # Player selection
        st.markdown("### 🔍 Player Analysis")
        
        # Input for player ID
        player_id = st.number_input(
            "Enter Player ID",
            min_value=1,
            value=2544,  # Default to LeBron James
            help="Enter the player ID to analyze historical trends"
        )
        
        # Optional: Player name input for display
        player_name = st.text_input(
            "Player Name (for display)",
            value="LeBron James",
            help="Enter player name for better display (optional)"
        )
        
        # Analyze button
        if st.button("📊 Analyze Historical Trends", type="primary"):
            with st.spinner("Fetching historical data..."):
                try:
                    # Test API connection first
                    health_response = requests.get(f"{api_base_url}/", timeout=5)
                    
                    if health_response.status_code == 200:
                        st.success("✅ Connected to API successfully")
                        
                        # Render the historical trends
                        render_player_historical_trends(
                            player_id=player_id,
                            player_name=player_name,
                            api_base_url=api_base_url,
                            seasons_back=seasons_back
                        )
                    else:
                        st.error(f"❌ API connection failed: {health_response.status_code}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to API. Please ensure the backend server is running.")
                    st.markdown("""
                    **To start the backend server:**
                    ```bash
                    cd /path/to/the_lineup
                    uvicorn app.main:app --reload
                    ```
                    """)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    with col_info:
        # Feature information
        st.markdown("### ℹ️ Feature Details")
        
        with st.expander("📊 Supported Statistics"):
            st.markdown("""
            **Offensive Stats:**
            - Points per game
            - Rebounds per game
            - Assists per game
            - 3-pointers made
            
            **Defensive Stats:**
            - Steals per game
            - Blocks per game
            - Turnovers per game
            
            **Efficiency Stats:**
            - Field goal percentage
            - Free throw percentage
            """)
        
        with st.expander("📈 Trend Classifications"):
            st.markdown("""
            **Increasing** 📈: Stat trending upward
            
            **Decreasing** 📉: Stat trending downward
            
            **Stable** ➡️: Stat relatively consistent
            
            **Volatile** 📊: Stat with high variability
            """)
        
        with st.expander("🔧 Technical Details"):
            st.markdown("""
            - **Trend Analysis**: Linear regression slope
            - **Volatility Detection**: Coefficient of variation
            - **Data Source**: NBA Stats API
            - **Update Frequency**: Daily during season
            - **Historical Range**: Up to 5 seasons
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    ### 🚀 Next Steps
    
    This historical trends feature can be integrated into:
    - **Player detail pages** in the draft interface
    - **Player comparison tools**
    - **Draft strategy recommendations**
    - **Injury risk assessment** (based on volatility)
    - **Breakout player identification** (based on trends)
    """)

if __name__ == "__main__":
    main() 