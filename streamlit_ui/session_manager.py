"""
LCS Engine - Session Manager (Supabase-backed)
Replaces the file-based session manager with database persistence.

This module provides the same interface as your original session_manager.py
but stores data in Supabase instead of local files.
"""

import streamlit as st # type: ignore
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

# Import our database module
from database import LCSDatabase, auto_save_session # type: ignore


class SessionManager:
    """
    Manages user sessions with Supabase persistence.
    
    Key changes from file-based version:
    - Sessions are stored in Supabase, not local files
    - Users identified by username, not random session ID
    - Sessions persist across deploys and devices
    """
    
    def __init__(self):
        self.db = LCSDatabase()
        self._current_username: Optional[str] = None
    
    @property
    def is_connected(self) -> bool:
        """Check if database is available"""
        return self.db.is_connected()
    
    def generate_session_id(self) -> str:
        """
        Generate a unique session ID.
        Note: With Supabase, we use usernames instead of random IDs,
        but keeping this for backwards compatibility.
        """
        return str(uuid.uuid4())[:8]
    
    def set_current_user(self, username: str):
        """Set the current logged-in user"""
        self._current_username = username.lower().strip()
        st.session_state.logged_in_user = self._current_username
    
    def get_current_user(self) -> Optional[str]:
        """Get the current logged-in user"""
        return st.session_state.get("logged_in_user") or self._current_username
    
    def load_session(self, username: str) -> bool:
        """
        Load a session by username.
        
        Args:
            username: The user's identifier
            
        Returns:
            True if session was loaded successfully
        """
        session = self.db.get_session(username)
        
        if session:
            self.db.restore_session_to_streamlit(session["session_data"])
            self.set_current_user(username)
            return True
        
        return False
    
    def save_session(self, username: Optional[str] = None) -> bool:
        """
        Save the current session to database.
        
        Args:
            username: Optional username override (uses current user if not provided)
            
        Returns:
            True if saved successfully
        """
        user = username or self.get_current_user()
        
        if not user:
            return False
        
        session_data = self.db.extract_session_data_from_streamlit()
        return self.db.save_session(user, session_data)
    
    def create_new_session(self, username: str) -> bool:
        """
        Create a new session for a user.
        
        Args:
            username: The user's identifier
            
        Returns:
            True if created successfully
        """
        if self.db.create_session(username):
            self.set_current_user(username)
            self._initialize_session_state()
            return True
        return False
    
    def session_exists(self, username: str) -> bool:
        """Check if a session exists for a username"""
        return self.db.session_exists(username)
    
    def get_session_url(self, username: Optional[str] = None) -> str:
        """
        Get a shareable URL for the session.
        
        Note: With database persistence, users just need their username,
        not a special URL. But keeping this for UI compatibility.
        """
        # Save before generating URL
        self.save_session(username)
        
        user = username or self.get_current_user()
        if user:
            return f"Just remember your username: {user}"
        
        return "Please log in to save your progress."
    
    def _initialize_session_state(self):
        """Initialize default session state values"""
        defaults = {
            "user_profile": {},
            "quiz_completed": False,
            "quiz_step": 1,
            "quiz_answers": {},
            "strategies": [],
            "selected_strategy": None,
            "chat_messages": [],
            "portfolio": {},
            "trade_history": [],
            "initial_investment": 10000
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value


# =========================================================================
# UPDATED SESSION UTILS (drop-in replacement for your session_utils.py)
# =========================================================================

# Global session manager instance
_session_manager: Optional[SessionManager] = None

def get_session_manager() -> SessionManager:
    """Get or create the session manager singleton"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def init_session() -> bool:
    """
    Initialize or restore session.
    
    New flow:
    1. Check if user is already logged in (session_state)
    2. If not, show login UI
    3. If yes, ensure session state is populated
    
    Returns:
        True if session was restored from database
    """
    sm = get_session_manager()
    
    # Already logged in?
    current_user = sm.get_current_user()
    
    if current_user:
        # Make sure session state is initialized
        if "quiz_completed" not in st.session_state:
            sm.load_session(current_user)
            return True
        return False
    
    # Check URL params for legacy support
    query_params = st.query_params
    session_param = query_params.get("session") or query_params.get("user")
    
    if session_param:
        if sm.load_session(session_param):
            st.query_params.clear()  # Clean URL
            return True
    
    return False


def save_session():
    """Save current session to database"""
    sm = get_session_manager()
    sm.save_session()


def get_shareable_link() -> str:
    """Get shareable link (now just returns username reminder)"""
    sm = get_session_manager()
    return sm.get_session_url()


def display_session_info():
    """Display session information in the UI"""
    sm = get_session_manager()
    current_user = sm.get_current_user()
    
    if not current_user:
        return
    
    with st.expander("📌 Your Session", expanded=False):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"**Logged in as:** {current_user}")
            st.caption("Your progress is automatically saved. Just remember your username to return!")
        
        with col2:
            if st.button("💾 Save Now", key="manual_save_btn"):
                if sm.save_session():
                    st.success("Saved!")
                else:
                    st.error("Save failed")
        
        # Connection status
        if sm.is_connected:
            st.caption("✅ Connected to database")
        else:
            st.caption("⚠️ Demo mode - progress won't persist")


def render_login_screen() -> bool:
    """
    Render login screen and handle authentication.
    
    Returns:
        True if user is logged in, False if login screen is showing
        
    Usage in app.py:
        from session_manager import render_login_screen, init_session
        
        # At the start of your app:
        if not render_login_screen():
            st.stop()  # Don't render rest of app until logged in
        
        # User is now logged in, continue with app...
    """
    sm = get_session_manager()
    
    # Already logged in?
    if sm.get_current_user():
        return True
    
    # Show login UI
    st.markdown("## 👋 Welcome to LCS Engine")
    st.markdown("**Learn. Choose. Strategize.**")
    st.markdown("---")
    
    st.markdown("Enter your name to get started. If you've used LCS before, enter the same name to restore your progress.")
    
    # Login form
    with st.form("login_form"):
        username = st.text_input(
            "Your Name",
            placeholder="e.g., maria_2025",
            help="Use something memorable! This is how you'll log back in."
        )
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("Continue →", type="primary", use_container_width=True)
    
    if submit and username:
        clean_username = username.lower().strip().replace(" ", "_")
        
        # Validate
        if len(clean_username) < 3:
            st.error("Please enter at least 3 characters.")
            return False
        
        if not clean_username.replace("_", "").isalnum():
            st.error("Please use only letters, numbers, and underscores.")
            return False
        
        # Check if returning user
        if sm.session_exists(clean_username):
            if sm.load_session(clean_username):
                st.success(f"Welcome back, {clean_username}! 🎉")
                st.balloons()
                st.rerun()
        else:
            # New user
            if sm.create_new_session(clean_username):
                st.success(f"Welcome, {clean_username}! Let's get started. 🚀")
                st.rerun()
            else:
                st.error("Could not create session. Please try again.")
        
        return False
    
    # Show demo mode warning if not connected
    if not sm.is_connected:
        st.warning("""
        ⚠️ **Demo Mode**: Database not connected. 
        Your progress won't be saved between sessions.
        """)
    
    return False


def logout():
    """Log out the current user"""
    sm = get_session_manager()
    
    # Save before logging out
    sm.save_session()
    
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    st.rerun()


# =========================================================================
# AUTO-SAVE DECORATOR
# =========================================================================

def auto_save_on_change(func):
    """
    Decorator to automatically save session after a function runs.
    
    Usage:
        @auto_save_on_change
        def complete_quiz():
            st.session_state.quiz_completed = True
            # ... process quiz results
    """
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        save_session()
        return result
    return wrapper
