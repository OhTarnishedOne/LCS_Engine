"""
LCS Engine - Supabase Database Module
Handles persistent session storage for the W!se pilot program.

Setup Instructions:
1. Create a free Supabase account at https://supabase.com
2. Create a new project
3. Run the SQL below in Supabase SQL Editor to create the table
4. Copy your project URL and anon key to Streamlit secrets

Required SQL (run in Supabase SQL Editor):
-----------------------------------------
CREATE TABLE lcs_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    session_data JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast username lookups
CREATE INDEX idx_sessions_username ON lcs_sessions(username);

-- Auto-update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_lcs_sessions_updated_at 
    BEFORE UPDATE ON lcs_sessions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
-----------------------------------------

Streamlit Secrets (add to .streamlit/secrets.toml or Streamlit Cloud):
----------------------------------------------------------------------
[supabase]
url = "https://your-project-id.supabase.co"
key = "your-anon-key-here"
----------------------------------------------------------------------
"""

import streamlit as st # type: ignore
from typing import Optional, Dict, Any
from datetime import datetime
import json

# Try to import supabase - will need to add to requirements.txt
try:
    from supabase import create_client, Client # type: ignore
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


class LCSDatabase:
    """
    Database client for LCS session persistence.
    Uses Supabase as the backend, with graceful fallback to local-only mode.
    """
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.demo_mode = True
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client from Streamlit secrets"""
        if not SUPABASE_AVAILABLE:
            st.warning("⚠️ Supabase not installed. Run: pip install supabase")
            return
        
        try:
            # Try to get credentials from Streamlit secrets
            supabase_url = st.secrets.get("supabase", {}).get("url")
            supabase_key = st.secrets.get("supabase", {}).get("key")
            
            if supabase_url and supabase_key:
                self.client = create_client(supabase_url, supabase_key)
                self.demo_mode = False
            else:
                # Check environment variables as fallback
                import os
                supabase_url = os.getenv("SUPABASE_URL")
                supabase_key = os.getenv("SUPABASE_KEY")
                
                if supabase_url and supabase_key:
                    self.client = create_client(supabase_url, supabase_key)
                    self.demo_mode = False
        except Exception as e:
            st.warning(f"⚠️ Database connection failed: {e}. Running in demo mode.")
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.client is not None and not self.demo_mode
    
    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================
    
    def get_session(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a session by username.
        
        Args:
            username: The student's unique identifier (e.g., "maria_2025")
            
        Returns:
            Session data dict if found, None otherwise
        """
        if not self.is_connected():
            return None
        
        try:
            response = self.client.table("lcs_sessions") \
                .select("*") \
                .eq("username", username.lower().strip()) \
                .execute()
            
            if response.data and len(response.data) > 0:
                row = response.data[0]
                return {
                    "id": row["id"],
                    "username": row["username"],
                    "session_data": row["session_data"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
            return None
            
        except Exception as e:
            st.error(f"Error retrieving session: {e}")
            return None
    
    def create_session(self, username: str, session_data: Dict[str, Any] = None) -> bool:
        """
        Create a new session for a user.
        
        Args:
            username: The student's unique identifier
            session_data: Initial session data (optional)
            
        Returns:
            True if created successfully, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            # Sanitize username
            clean_username = username.lower().strip()
            
            # Prepare session data
            data = {
                "username": clean_username,
                "session_data": session_data or self._get_default_session_data()
            }
            
            response = self.client.table("lcs_sessions").insert(data).execute()
            return len(response.data) > 0
            
        except Exception as e:
            # Check if it's a duplicate key error
            if "duplicate key" in str(e).lower():
                st.warning(f"Username '{username}' already exists. Try logging in instead.")
            else:
                st.error(f"Error creating session: {e}")
            return False
    
    def update_session(self, username: str, session_data: Dict[str, Any]) -> bool:
        """
        Update an existing session.
        
        Args:
            username: The student's unique identifier
            session_data: Updated session data
            
        Returns:
            True if updated successfully, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            response = self.client.table("lcs_sessions") \
                .update({"session_data": session_data}) \
                .eq("username", username.lower().strip()) \
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            st.error(f"Error updating session: {e}")
            return False
    
    def save_session(self, username: str, session_data: Dict[str, Any]) -> bool:
        """
        Save session data - creates if new, updates if exists (upsert).
        
        Args:
            username: The student's unique identifier
            session_data: Session data to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            clean_username = username.lower().strip()
            
            # Use upsert to handle both create and update
            response = self.client.table("lcs_sessions") \
                .upsert({
                    "username": clean_username,
                    "session_data": session_data
                }, on_conflict="username") \
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            st.error(f"Error saving session: {e}")
            return False
    
    def delete_session(self, username: str) -> bool:
        """
        Delete a session (use with caution).
        
        Args:
            username: The student's unique identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            response = self.client.table("lcs_sessions") \
                .delete() \
                .eq("username", username.lower().strip()) \
                .execute()
            
            return True
            
        except Exception as e:
            st.error(f"Error deleting session: {e}")
            return False
    
    def session_exists(self, username: str) -> bool:
        """
        Check if a session exists for a username.
        
        Args:
            username: The student's unique identifier
            
        Returns:
            True if session exists, False otherwise
        """
        return self.get_session(username) is not None
    
    # =========================================================================
    # SESSION DATA HELPERS
    # =========================================================================
    
    def _get_default_session_data(self) -> Dict[str, Any]:
        """Return default session data structure for new users"""
        return {
            "user_profile": {},
            "quiz_completed": False,
            "quiz_step": 1,
            "quiz_answers": {},
            "strategies": [],
            "selected_strategy": None,
            "chat_messages": [],
            "portfolio": {},
            "trade_history": [],
            "initial_investment": 10000,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
    
    def extract_session_data_from_streamlit(self) -> Dict[str, Any]:
        """
        Extract current session data from Streamlit session_state.
        Call this before saving to database.
        """
        return {
            "user_profile": dict(st.session_state.get("user_profile", {})),
            "quiz_completed": st.session_state.get("quiz_completed", False),
            "quiz_step": st.session_state.get("quiz_step", 1),
            "quiz_answers": dict(st.session_state.get("quiz_answers", {})),
            "strategies": list(st.session_state.get("strategies", [])),
            "selected_strategy": st.session_state.get("selected_strategy"),
            "chat_messages": list(st.session_state.get("chat_messages", [])),
            "portfolio": dict(st.session_state.get("portfolio", {})),
            "trade_history": list(st.session_state.get("trade_history", [])),
            "initial_investment": st.session_state.get("initial_investment", 10000),
            "last_activity": datetime.now().isoformat()
        }
    
    def restore_session_to_streamlit(self, session_data: Dict[str, Any]):
        """
        Restore session data to Streamlit session_state.
        Call this after loading from database.
        """
        st.session_state.user_profile = session_data.get("user_profile", {})
        st.session_state.quiz_completed = session_data.get("quiz_completed", False)
        st.session_state.quiz_step = session_data.get("quiz_step", 1)
        st.session_state.quiz_answers = session_data.get("quiz_answers", {})
        st.session_state.strategies = session_data.get("strategies", [])
        st.session_state.selected_strategy = session_data.get("selected_strategy")
        st.session_state.chat_messages = session_data.get("chat_messages", [])
        st.session_state.portfolio = session_data.get("portfolio", {})
        st.session_state.trade_history = session_data.get("trade_history", [])
        st.session_state.initial_investment = session_data.get("initial_investment", 10000)
    
    # =========================================================================
    # ANALYTICS (for W!se pilot reporting)
    # =========================================================================
    
    def get_all_sessions(self) -> list:
        """
        Get all sessions (for admin/reporting purposes).
        Useful for generating the W!se pilot learning impact report.
        """
        if not self.is_connected():
            return []
        
        try:
            response = self.client.table("lcs_sessions") \
                .select("*") \
                .order("created_at", desc=True) \
                .execute()
            
            return response.data or []
            
        except Exception as e:
            st.error(f"Error retrieving sessions: {e}")
            return []
    
    def get_session_count(self) -> int:
        """Get total number of sessions (active students)"""
        if not self.is_connected():
            return 0
        
        try:
            response = self.client.table("lcs_sessions") \
                .select("id", count="exact") \
                .execute()
            
            return response.count or 0
            
        except Exception as e:
            return 0
    
    def get_completed_quiz_count(self) -> int:
        """Get number of students who completed the quiz"""
        if not self.is_connected():
            return 0
        
        try:
            # This requires a more complex query - for now, fetch all and filter
            sessions = self.get_all_sessions()
            return sum(1 for s in sessions if s.get("session_data", {}).get("quiz_completed", False))
        except:
            return 0


# =========================================================================
# STREAMLIT UI COMPONENTS
# =========================================================================

def render_login_ui(db: LCSDatabase) -> Optional[str]:
    """
    Render the login/signup UI for session management.
    Returns the username if logged in, None otherwise.
    
    Usage in your app.py:
        from database import LCSDatabase, render_login_ui
        
        db = LCSDatabase()
        username = render_login_ui(db)
        
        if username:
            # User is logged in, show the app
            st.write(f"Welcome, {username}!")
        else:
            # User needs to log in
            st.stop()
    """
    
    # Check if already logged in
    if st.session_state.get("logged_in_user"):
        return st.session_state.logged_in_user
    
    st.markdown("## 👋 Welcome to LCS Engine")
    st.markdown("Enter your name to save your progress and return later.")
    
    # Simple username input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        username = st.text_input(
            "Your Name or ID",
            placeholder="e.g., maria_wise2025",
            help="Use something you'll remember! This is how you'll log back in.",
            key="login_username_input"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        login_clicked = st.button("Continue →", type="primary", use_container_width=True)
    
    if login_clicked and username:
        clean_username = username.lower().strip()
        
        if len(clean_username) < 3:
            st.error("Please enter at least 3 characters.")
            return None
        
        # Check if user exists
        existing_session = db.get_session(clean_username)
        
        if existing_session:
            # Restore existing session
            db.restore_session_to_streamlit(existing_session["session_data"])
            st.session_state.logged_in_user = clean_username
            st.success(f"Welcome back, {clean_username}! Your progress has been restored.")
            st.rerun()
        else:
            # Create new session
            if db.create_session(clean_username):
                st.session_state.logged_in_user = clean_username
                st.success(f"Welcome, {clean_username}! Your new session has been created.")
                st.rerun()
            else:
                st.error("Could not create session. Please try again.")
        
        return None
    
    # Demo mode warning
    if db.demo_mode:
        st.warning("""
        ⚠️ **Demo Mode**: Database not connected. Your progress won't be saved between sessions.
        
        To enable persistence, add Supabase credentials to your Streamlit secrets.
        """)
    
    return None


def auto_save_session(db: LCSDatabase):
    """
    Auto-save current session to database.
    Call this after important user actions (quiz completion, strategy selection, etc.)
    
    Usage:
        from database import LCSDatabase, auto_save_session
        
        db = LCSDatabase()
        
        # After user completes quiz:
        st.session_state.quiz_completed = True
        auto_save_session(db)
    """
    username = st.session_state.get("logged_in_user")
    
    if username and db.is_connected():
        session_data = db.extract_session_data_from_streamlit()
        db.save_session(username, session_data)


# =========================================================================
# QUICK TEST
# =========================================================================

if __name__ == "__main__":
    # Quick test to verify the module works
    print("LCS Database Module")
    print("=" * 50)
    print(f"Supabase library available: {SUPABASE_AVAILABLE}")
    print("\nTo use this module:")
    print("1. pip install supabase")
    print("2. Add credentials to .streamlit/secrets.toml")
    print("3. Import and use in your Streamlit app")
