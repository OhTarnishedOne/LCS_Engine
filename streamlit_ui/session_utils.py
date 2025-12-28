"""
Session utilities for managing persistent sessions in Streamlit
"""

import streamlit as st
from session_manager import SessionManager
from typing import Optional

# Initialize session manager
session_manager = SessionManager()

def init_session():
    """Initialize or restore session based on URL parameters"""
    
    # Check for session ID in URL parameters
    query_params = st.query_params
    session_id = query_params.get('session')
    
    # Initialize session_restored flag
    if 'session_restored' not in st.session_state:
        st.session_state.session_restored = False
    
    # If session ID in URL and not yet restored
    if session_id and not st.session_state.session_restored:
        # Try to load the session
        if session_manager.load_session(session_id):
            st.session_state.session_restored = True
            st.session_state.session_loaded_from_url = True
            return True
        else:
            # Invalid session ID, clear it from URL
            st.query_params.clear()
            st.warning("Session not found or expired. Starting a new session.")
    
    # Initialize new session if needed
    if 'session_id' not in st.session_state:
        st.session_state.session_id = session_manager.generate_session_id()
        st.session_state.session_loaded_from_url = False
        
        # Initialize default values
        if 'user_profile' not in st.session_state:
            st.session_state.user_profile = {}
        if 'strategies' not in st.session_state:
            st.session_state.strategies = []
        if 'quiz_completed' not in st.session_state:
            st.session_state.quiz_completed = False
        if 'quiz_step' not in st.session_state:
            st.session_state.quiz_step = 1
        if 'quiz_answers' not in st.session_state:
            st.session_state.quiz_answers = {}
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        if 'selected_strategy' not in st.session_state:
            st.session_state.selected_strategy = None
        if 'portfolio' not in st.session_state:
            st.session_state.portfolio = {}
        if 'trade_history' not in st.session_state:
            st.session_state.trade_history = []
        if 'initial_investment' not in st.session_state:
            st.session_state.initial_investment = 10000
    
    return False

def save_session():
    """Save current session to database"""
    if 'session_id' in st.session_state:
        session_manager.save_session(st.session_state.session_id)

def get_shareable_link() -> str:
    """Get the shareable link for current session"""
    save_session()  # Auto-save before generating link
    return session_manager.get_session_url(st.session_state.get('session_id'))

def display_session_info():
    """Display session information and shareable link in the UI"""
    if 'session_id' not in st.session_state:
        return
    
    with st.expander("📌 Session Info", expanded=False):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            shareable_link = get_shareable_link()
            st.text_input(
                "Your Session Link (bookmark or share this):",
                value=shareable_link,
                key="session_link_display",
                help="Save this link to return to your session later",
                disabled=True
            )
        
        with col2:
            if st.button("📋 Copy Link", key="copy_link_btn"):
                st.write(f"```{shareable_link}```")
                st.success("Link displayed above - copy it manually")
        
        # Show session status
        if st.session_state.get('session_loaded_from_url'):
            st.success("✅ Session restored successfully!")
            st.session_state.session_loaded_from_url = False
        
        # Auto-save indicator
        st.caption(f"Session ID: {st.session_state.session_id} | Auto-saving enabled")

def auto_save_decorator(func):
    """Decorator to auto-save session after certain actions"""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        save_session()
        return result
    return wrapper