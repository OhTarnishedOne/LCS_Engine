#!/bin/bash

# Script to run LCS app with live API connections

echo "🟢 Starting LCS in LIVE MODE..."
echo "----------------------------------------"
echo "This mode uses real API connections."
echo "Make sure API keys are configured!"
echo "----------------------------------------"

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "📁 Loading API keys from .env file..."
    source .env
else
    echo "⚠️  No .env file found. Using system environment or Streamlit secrets."
fi

# Force live mode
export LCS_DEMO_MODE=false

# Run the Streamlit app
streamlit run app.py --server.port 8501