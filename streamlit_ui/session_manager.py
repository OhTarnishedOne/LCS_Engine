"""
Session persistence manager for LCS Engine
Handles saving and loading user sessions with SQLite
"""

import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def datetime_decoder(dct):
    """Decode ISO format strings back to datetime objects"""
    for key, value in dct.items():
        if isinstance(value, str):
            # Try to parse ISO format datetime strings
            try:
                # Check if it looks like an ISO datetime string
                if 'T' in value and len(value) > 15:
                    dct[key] = datetime.fromisoformat(value)
            except (ValueError, AttributeError):
                pass
    return dct

try:
    import streamlit as st
except ImportError:
    # For testing purposes when streamlit is not available
    class MockST:
        class session_state:
            pass
        @staticmethod
        def get_option(key):
            return "localhost" if key == "browser.serverAddress" else "8501"
    st = MockST()

class SessionManager:
    def __init__(self, db_path: str = "lcs_sessions.db"):
        """Initialize the session manager with SQLite database"""
        self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self):
        """Create the sessions table if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_profile TEXT,
                    quiz_answers TEXT,
                    quiz_completed BOOLEAN,
                    quiz_step INTEGER,
                    strategies TEXT,
                    selected_strategy TEXT,
                    chat_messages TEXT,
                    portfolio TEXT,
                    trade_history TEXT,
                    initial_investment REAL,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    last_accessed TIMESTAMP
                )
            """)
            conn.commit()
    
    def generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return str(uuid.uuid4())[:8]  # Short ID for easier sharing
    
    def save_session(self, session_id: Optional[str] = None) -> str:
        """Save current Streamlit session state to database"""
        if not session_id:
            session_id = st.session_state.get('session_id')
            if not session_id:
                session_id = self.generate_session_id()
                st.session_state.session_id = session_id
        
        # Prepare session data
        session_data = {
            'user_profile': json.dumps(st.session_state.get('user_profile', {}), cls=DateTimeEncoder),
            'quiz_answers': json.dumps(st.session_state.get('quiz_answers', {}), cls=DateTimeEncoder),
            'quiz_completed': st.session_state.get('quiz_completed', False),
            'quiz_step': st.session_state.get('quiz_step', 1),
            'strategies': json.dumps(st.session_state.get('strategies', []), cls=DateTimeEncoder),
            'selected_strategy': json.dumps(st.session_state.get('selected_strategy', None), cls=DateTimeEncoder),
            'chat_messages': json.dumps(st.session_state.get('chat_messages', []), cls=DateTimeEncoder),
            'portfolio': json.dumps(st.session_state.get('portfolio', {}), cls=DateTimeEncoder),
            'trade_history': json.dumps(st.session_state.get('trade_history', []), cls=DateTimeEncoder),
            'initial_investment': st.session_state.get('initial_investment', 10000),
        }
        
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            # Check if session exists
            existing = conn.execute(
                "SELECT session_id FROM sessions WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            
            if existing:
                # Update existing session
                conn.execute("""
                    UPDATE sessions SET
                        user_profile = ?,
                        quiz_answers = ?,
                        quiz_completed = ?,
                        quiz_step = ?,
                        strategies = ?,
                        selected_strategy = ?,
                        chat_messages = ?,
                        portfolio = ?,
                        trade_history = ?,
                        initial_investment = ?,
                        updated_at = ?,
                        last_accessed = ?
                    WHERE session_id = ?
                """, (
                    session_data['user_profile'],
                    session_data['quiz_answers'],
                    session_data['quiz_completed'],
                    session_data['quiz_step'],
                    session_data['strategies'],
                    session_data['selected_strategy'],
                    session_data['chat_messages'],
                    session_data['portfolio'],
                    session_data['trade_history'],
                    session_data['initial_investment'],
                    now,
                    now,
                    session_id
                ))
            else:
                # Create new session
                conn.execute("""
                    INSERT INTO sessions (
                        session_id, user_profile, quiz_answers, quiz_completed,
                        quiz_step, strategies, selected_strategy, chat_messages,
                        portfolio, trade_history, initial_investment,
                        created_at, updated_at, last_accessed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    session_data['user_profile'],
                    session_data['quiz_answers'],
                    session_data['quiz_completed'],
                    session_data['quiz_step'],
                    session_data['strategies'],
                    session_data['selected_strategy'],
                    session_data['chat_messages'],
                    session_data['portfolio'],
                    session_data['trade_history'],
                    session_data['initial_investment'],
                    now,
                    now,
                    now
                ))
            
            conn.commit()
        
        return session_id
    
    def load_session(self, session_id: str) -> bool:
        """Load session from database into Streamlit session state"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            
            if not row:
                return False
            
            # Update last accessed time
            conn.execute(
                "UPDATE sessions SET last_accessed = ? WHERE session_id = ?",
                (datetime.now().isoformat(), session_id)
            )
            conn.commit()
            
            # Restore session state
            st.session_state.session_id = session_id
            st.session_state.user_profile = json.loads(row['user_profile'] or '{}', object_hook=datetime_decoder)
            st.session_state.quiz_answers = json.loads(row['quiz_answers'] or '{}', object_hook=datetime_decoder)
            st.session_state.quiz_completed = bool(row['quiz_completed'])
            st.session_state.quiz_step = row['quiz_step'] or 1
            st.session_state.strategies = json.loads(row['strategies'] or '[]', object_hook=datetime_decoder)
            st.session_state.selected_strategy = json.loads(row['selected_strategy'] or 'null', object_hook=datetime_decoder)
            st.session_state.chat_messages = json.loads(row['chat_messages'] or '[]', object_hook=datetime_decoder)
            st.session_state.portfolio = json.loads(row['portfolio'] or '{}', object_hook=datetime_decoder)
            st.session_state.trade_history = json.loads(row['trade_history'] or '[]', object_hook=datetime_decoder)
            st.session_state.initial_investment = row['initial_investment'] or 10000
            
            return True
    
    def get_session_url(self, session_id: Optional[str] = None) -> str:
        """Generate a shareable URL for the session"""
        if not session_id:
            session_id = getattr(st.session_state, 'session_id', '') if hasattr(st, 'session_state') else ''
        
        # Get the current URL from Streamlit
        # In production, this would be your deployed URL
        base_url = "https://lcs-engine.streamlit.app"
        
        # For local development, use localhost
        try:
            if hasattr(st, 'get_option') and "localhost" in st.get_option("browser.serverAddress"):
                base_url = f"http://localhost:{st.get_option('browser.serverPort')}"
        except:
            # Default to production URL if can't determine
            pass
        
        return f"{base_url}/?session={session_id}"
    
    def cleanup_old_sessions(self, days: int = 30):
        """Remove sessions older than specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM sessions WHERE last_accessed < ?",
                (cutoff_date,)
            )
            conn.commit()
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT session_id, created_at, updated_at, last_accessed,
                       quiz_completed, user_profile
                FROM sessions WHERE session_id = ?
            """, (session_id,)).fetchone()
            
            if not row:
                return None
            
            user_profile = json.loads(row['user_profile'] or '{}')
            
            return {
                'session_id': row['session_id'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'last_accessed': row['last_accessed'],
                'quiz_completed': bool(row['quiz_completed']),
                'investor_type': user_profile.get('investor_type', 'Unknown')
            }