#!/bin/bash

# Script to run LCS app in demo mode for presentations

echo "🎮 Starting LCS in DEMO MODE..."
echo "----------------------------------------"
echo "This mode uses simulated data - perfect for demos!"
echo "No API keys required."
echo "----------------------------------------"

# Force demo mode
export LCS_DEMO_MODE=true

# Run the Streamlit app
streamlit run app.py --server.port 8501