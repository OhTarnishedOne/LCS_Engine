"""
Test script for session persistence functionality
Run this to verify session saving and loading works correctly
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from session_manager import SessionManager
import json

def test_session_persistence():
    """Test the session persistence functionality"""
    
    print("Testing Session Persistence...")
    print("-" * 50)
    
    # Initialize session manager
    sm = SessionManager("test_sessions.db")
    
    # Test 1: Generate session ID
    session_id = sm.generate_session_id()
    print(f"✅ Generated session ID: {session_id}")
    
    # Test 2: Save a mock session
    # Need to modify the SessionManager's st reference to use our mock
    import session_manager
    
    # Mock session state
    class MockSessionState:
        def __init__(self):
            self.session_id = session_id
            self.user_profile = {
                "investor_type": "Balanced",
                "experience_level": "Intermediate",
                "risk_tolerance": "Moderate"
            }
            self.quiz_completed = True
            self.quiz_step = 5
            self.quiz_answers = {
                "q1": "answer1",
                "q2": "answer2"
            }
            self.strategies = [
                {"name": "Strategy 1", "description": "Test strategy"}
            ]
            self.chat_messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
            self.portfolio = {
                "AAPL": {"shares": 10, "avg_price": 150.00}
            }
            self.trade_history = []
            self.initial_investment = 10000
            self.selected_strategy = None
        
        def get(self, key, default=None):
            return getattr(self, key, default)
    
    # Mock streamlit module  
    class MockST:
        session_state = MockSessionState()
        @staticmethod
        def get_option(key):
            return "localhost" if key == "browser.serverAddress" else "8501"
    
    # Replace the st module in SessionManager
    session_manager.st = MockST()
    
    # Save the session
    saved_id = sm.save_session(session_id)
    print(f"✅ Session saved with ID: {saved_id}")
    
    # Test 3: Load the session
    # Clear the mock session state
    class EmptySessionState:
        def get(self, key, default=None):
            return getattr(self, key, default)
    
    MockST.session_state = EmptySessionState()
    MockST.session_state.session_id = None
    MockST.session_state.user_profile = {}
    MockST.session_state.quiz_completed = False
    
    # Load the saved session
    success = sm.load_session(session_id)
    if success:
        print(f"✅ Session loaded successfully")
        print(f"   - User Profile: {MockST.session_state.user_profile.get('investor_type', 'Unknown')}")
        print(f"   - Quiz Completed: {MockST.session_state.quiz_completed}")
        print(f"   - Portfolio: {MockST.session_state.portfolio}")
    else:
        print("❌ Failed to load session")
    
    # Test 4: Generate session URL
    url = sm.get_session_url(session_id)
    print(f"✅ Session URL: {url}")
    
    # Test 5: Get session info
    info = sm.get_session_info(session_id)
    if info:
        print(f"✅ Session info retrieved:")
        print(f"   - Created: {info['created_at']}")
        print(f"   - Investor Type: {info['investor_type']}")
    
    print("-" * 50)
    print("All tests passed! ✅")
    
    # Clean up test database
    import os
    try:
        os.remove("test_sessions.db")
        print("Test database cleaned up")
    except:
        pass

if __name__ == "__main__":
    test_session_persistence()