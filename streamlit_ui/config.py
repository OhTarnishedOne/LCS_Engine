"""
Configuration file for LCS Streamlit App
Handles API keys and demo mode settings
"""

import os
import streamlit as st # type: ignore
from typing import Optional, Dict

class Config:
    """Central configuration manager"""
    
    def __init__(self):
        self.demo_mode = self._check_demo_mode()
        self.api_keys = self._load_api_keys()
    
    def _check_demo_mode(self) -> bool:
        """
        Check if app should run in demo mode
        Demo mode is OFF if any API key is found
        """
        # Force demo mode with environment variable
        if os.getenv('LCS_DEMO_MODE', '').lower() == 'true':
            return True
        
        # Check for any API key
        try:
            # Check Streamlit secrets
            if hasattr(st, 'secrets'):
                keys = st.secrets.get("api_keys", {})
                if any(keys.values()):
                    return False
            
            # Check environment variables
            api_env_vars = [
                'OPENAI_API_KEY',
                'CLAUDE_API_KEY',
                'ALPHA_VANTAGE_API_KEY',
                'APCA_API_KEY_ID',
                'POLYGON_API_KEY'
            ]
            
            if any(os.getenv(var) for var in api_env_vars):
                return False
                
        except Exception:
            pass
        
        # Default to demo mode if no keys found
        return True
    
    def _load_api_keys(self) -> Dict[str, Optional[str]]:
        """Load API keys from various sources"""
        keys = {}
        
        # Define key mappings
        key_mappings = {
            'openai': ['OPENAI_API_KEY'],
            'claude': ['CLAUDE_API_KEY'],
            'alpha_vantage': ['ALPHA_VANTAGE_API_KEY'],
            'alpaca_key': ['ALPACA_API_KEY', 'APCA_API_KEY_ID'],
            'alpaca_secret': ['ALPACA_SECRET_KEY', 'APCA_API_SECRET_KEY'],
            'polygon': ['POLYGON_API_KEY']
        }
        
        for key_name, env_vars in key_mappings.items():
            # Try Streamlit secrets first
            try:
                if hasattr(st, 'secrets'):
                    for var in env_vars:
                        value = st.secrets.get("api_keys", {}).get(var)
                        if value:
                            keys[key_name] = value
                            break
            except:
                pass
            
            # Fall back to environment variables
            if key_name not in keys:
                for var in env_vars:
                    value = os.getenv(var)
                    if value:
                        keys[key_name] = value
                        break
            
            # Set to None if not found
            if key_name not in keys:
                keys[key_name] = None
        
        return keys
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service"""
        return self.api_keys.get(service)
    
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode"""
        return self.demo_mode
    
    def get_mode_badge(self) -> str:
        """Get a badge indicating current mode"""
        if self.demo_mode:
            return "🎮 Demo Mode"
        else:
            return "🟢 Live Mode"
    
    def get_mode_message(self) -> str:
        """Get informative message about current mode"""
        if self.demo_mode:
            return "Running with simulated data. Perfect for demos and testing!"
        else:
            return "Connected to live APIs for real-time data and AI features."

# Global config instance
config = Config()

def show_mode_indicator():
    """Display mode indicator in the UI"""
    if config.is_demo_mode():
        st.info(f"**{config.get_mode_badge()}**: {config.get_mode_message()}")
    else:
        st.success(f"**{config.get_mode_badge()}**: {config.get_mode_message()}")

def force_demo_mode():
    """Force the app to run in demo mode regardless of API keys"""
    os.environ['LCS_DEMO_MODE'] = 'true'
    st.rerun()

def force_live_mode():
    """Force the app to use live APIs if keys are available"""
    os.environ['LCS_DEMO_MODE'] = 'false'
    st.rerun()