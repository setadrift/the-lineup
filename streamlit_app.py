"""
The Lineup - Streamlit Cloud Entry Point
Entry point for Streamlit Cloud deployment
"""

import os
import sys
import streamlit as st

# Configure page for wide layout
st.set_page_config(
    page_title="The Lineup - Fantasy Basketball Draft Assistant",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import and run the main Streamlit app
from app.frontend.streamlit.pages.draft_assistant_v2 import main

if __name__ == "__main__":
    main()
else:
    # When imported by Streamlit Cloud, just run main
    main() 