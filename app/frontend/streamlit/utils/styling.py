"""
The Lineup - Styling Utilities
Centralized styling management for Streamlit applications
"""

import os
import streamlit as st
from pathlib import Path


def load_css(css_file_path: str) -> str:
    """
    Load CSS content from a file.
    
    Args:
        css_file_path: Path to the CSS file
        
    Returns:
        CSS content as string
    """
    try:
        with open(css_file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"CSS file not found: {css_file_path}")
        return ""
    except Exception as e:
        st.error(f"Error loading CSS: {e}")
        return ""


def apply_main_styling():
    """
    Apply the main stylesheet to the current Streamlit page.
    """
    # Get the path to the CSS file
    current_dir = Path(__file__).parent
    css_path = current_dir.parent / "styles" / "main.css"
    
    # Load and apply CSS
    css_content = load_css(str(css_path))
    if css_content:
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def apply_custom_css(css_content: str):
    """
    Apply custom CSS content to the current page.
    
    Args:
        css_content: CSS content as string
    """
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def get_theme_colors():
    """
    Get the theme color palette for use in Python code.
    
    Returns:
        Dictionary of theme colors
    """
    return {
        'primary_orange': '#FF6B35',
        'primary_blue': '#2E86AB', 
        'secondary_orange': '#F7931E',
        'light_gray': '#F8F9FA',
        'medium_gray': '#E9ECEF',
        'dark_gray': '#6C757D',
        'text_dark': '#2E3440',
        'success_green': '#28A745',
        'warning_yellow': '#FFC107'
    } 