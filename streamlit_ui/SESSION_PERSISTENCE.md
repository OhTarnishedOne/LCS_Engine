# Session Persistence Implementation

## Overview
The LCS Engine now supports session persistence, allowing users to bookmark their progress and return later to continue where they left off.

## Features

### 1. Automatic Session Management
- Sessions are automatically created when users first visit the app
- All progress is saved to a local SQLite database
- Session data includes:
  - Quiz answers and completion status
  - User investment profile
  - Generated investment strategies
  - Chat conversation history
  - Paper trading portfolio and trades
  
### 2. Shareable Session URLs
- Each session gets a unique 8-character ID
- Users can bookmark the URL: `https://lcs-engine.streamlit.app/?session=abc123de`
- Session info is displayed at the top of the app with a copyable link

### 3. Auto-Save Functionality
Session data is automatically saved when:
- Quiz is completed
- Strategies are generated
- Chat messages are sent
- Trades are executed
- Any significant state change occurs

## Implementation Details

### Files Added
1. **session_manager.py** - Core session persistence logic
   - SQLite database management
   - Session save/load functionality
   - URL generation

2. **session_utils.py** - Utility functions for Streamlit integration
   - Session initialization
   - Auto-save decorator
   - UI components for displaying session info

3. **test_session.py** - Test suite for verifying functionality

### Database Schema
```sql
CREATE TABLE sessions (
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
```

### Modified Files
- **app.py** - Added session initialization and display
- **pages/1_Onboarding.py** - Added save after quiz completion
- **pages/2_Strategies.py** - Added save after strategy generation and chat
- **pages/3_Paper_Trade.py** - Added save after trade execution

## Usage

### For Users
1. Complete the quiz and generate strategies as normal
2. Look for the "📌 Session Info" expandable section at the top of the page
3. Copy the session link and bookmark it
4. Return anytime by visiting the bookmarked link
5. Your progress will be automatically restored

### For Developers
```python
from session_utils import init_session, save_session, display_session_info

# Initialize session (handles both new and restored)
session_restored = init_session()

# Save current session state
save_session()

# Display session info in UI
display_session_info()
```

## Deployment Notes

### Streamlit Cloud
The implementation uses SQLite which works well with Streamlit Cloud's persistent storage. The database file `lcs_sessions.db` will be created automatically.

### Local Development
For local testing, the session URLs will use `http://localhost:8501/?session=...`

## Future Enhancements

### Option 2: Email-Based Login
Could be added by:
1. Adding email field to sessions table
2. Implementing magic link generation and sending
3. Adding email verification endpoint

### Option 3: Full Authentication
Could be implemented using:
1. Streamlit-Authenticator library
2. Adding password hashing
3. User management interface

## Testing
Run the test suite:
```bash
cd streamlit_ui
python test_session.py
```

## Session Cleanup
Old sessions (>30 days) can be cleaned up using:
```python
from session_manager import SessionManager
sm = SessionManager()
sm.cleanup_old_sessions(days=30)
```

## Datetime Handling
The session manager properly handles datetime objects in portfolios and trade history:
- **Automatic serialization** - Datetime objects are converted to ISO format strings when saving
- **Automatic deserialization** - ISO format strings are converted back to datetime objects when loading
- **Nested support** - Works with datetime objects in nested data structures
- **No manual conversion needed** - Just use datetime objects normally in your session state