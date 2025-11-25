"""
LCS - Learn. Choose. Strategize.
Main Streamlit Application Entry Point
"""

import streamlit as st # pyright: ignore[reportMissingImports]
from pathlib import Path
import sys

# Add parent directory to path to access lcs_engine modules
sys.path.append(str(Path(__file__).parent.parent))

# Import config
from config import config, show_mode_indicator

# Page configuration
st.set_page_config(
    page_title="LCS - Learn. Choose. Strategize.",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(45deg, #2E7D32, #4CAF50);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #888;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: #1E1E1E;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #4CAF50;
        color: #E0E0E0;
    }
    .feature-card h4 {
        color: #4CAF50;
        margin-bottom: 1rem;
    }
    .feature-card ul {
        color: #E0E0E0;
    }
    .feature-card li {
        margin-bottom: 0.5rem;
    }
    .cta-button {
        background: #4CAF50;
        color: white;
        padding: 1rem 2rem;
        border-radius: 5px;
        text-decoration: none;
        display: inline-block;
        margin: 1rem 0;
    }
    .stats-box {
        background: #1E1E1E;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        text-align: center;
        border: 1px solid #333;
    }
    .stats-box h3 {
        color: #4CAF50;
        margin-bottom: 0.5rem;
    }
    .stats-box p {
        color: #B0B0B0;
        margin: 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {}
if 'strategies' not in st.session_state:
    st.session_state.strategies = []
if 'quiz_completed' not in st.session_state:
    st.session_state.quiz_completed = False

# Show mode indicator at the top of the page
show_mode_indicator()

# Sidebar navigation
with st.sidebar:
    st.markdown("## 🧭 Navigation")
    st.markdown("---")
    
    # Navigation options
    page = st.radio(
        "Choose your journey:",
        ["🏠 Home", "🎯 Start Quiz", "📊 View Strategies", "🎲 Paper Trade", "📚 Learn More"],
        index=0
    )
    
    # Show progress if quiz is started
    if st.session_state.quiz_completed:
        st.markdown("---")
        st.success("✅ Quiz Completed!")
        st.markdown("### Your Profile")
        if st.session_state.user_profile:
            for key, value in st.session_state.user_profile.items():
                st.write(f"**{key}:** {value}")

# Main content based on navigation
if page == "🏠 Home":
    # Hero Section
    st.markdown('<h1 class="main-header">LCS - Learn. Choose. Strategize.</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Investing, explained. Build personalized investment strategies, get AI explanations in plain English, and test them risk-free with live market data.</p>', unsafe_allow_html=True)
    
    # Value Proposition
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="stats-box">
            <h3>📚 Learn</h3>
            <p>Get personalized investment education tailored to your experience level</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stats-box">
            <h3>🎯 Choose</h3>
            <p>Receive AI-powered strategy recommendations based on your goals</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stats-box">
            <h3>📈 Strategize</h3>
            <p>Test your strategies risk-free with real market data</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # How It Works
    st.markdown("## 🔄 How It Works")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        ### 1️⃣ Take Our Quick Quiz
        Answer 3-5 simple questions about your investment goals, risk tolerance, and timeline. No jargon, just plain English.
        
        ### 2️⃣ Get Your Personalized Strategies
        Our AI analyzes your profile and generates 2-3 custom investment strategies with clear explanations of why each stock was selected.
        
        ### 3️⃣ Test Risk-Free
        Use our paper trading simulator to test your strategies with real market data. See how your portfolio would perform without risking a penny.
        """)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>💡 What Makes LCS Different?</h4>
            <ul>
                <li><strong>No intimidating jargon</strong> - Everything explained in plain English</li>
                <li><strong>Personalized to YOU</strong> - Not generic advice</li>
                <li><strong>Learn by doing</strong> - Practice with real market data</li>
                <li><strong>AI-powered insights</strong> - Get explanations for every recommendation</li>
                <li><strong>100% risk-free</strong> - Paper trade before investing real money</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Call to Action
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🚀 Ready to Start Your Investment Journey?")
        if st.button("Start the Quiz 🎯", type="primary", use_container_width=True):
            st.switch_page("pages/1_🎯_Onboarding.py")

elif page == "🎯 Start Quiz":
    st.switch_page("pages/1_🎯_Onboarding.py")

elif page == "📊 View Strategies":
    if not st.session_state.quiz_completed:
        st.warning("Please complete the quiz first to see your personalized strategies!")
        if st.button("Go to Quiz"):
            st.switch_page("pages/1_🎯_Onboarding.py")
    else:
        st.switch_page("pages/2_📊_Strategies.py")

elif page == "🎲 Paper Trade":
    if not st.session_state.strategies:
        st.warning("Please complete the quiz and view your strategies first!")
        if st.button("Go to Quiz"):
            st.switch_page("pages/1_🎯_Onboarding.py")
    else:
        st.switch_page("pages/3_🎲_Paper_Trade.py")

elif page == "📚 Learn More":
    st.markdown("## 📚 Investment Education Resources")
    
    # Educational content
    tab1, tab2, tab3 = st.tabs(["Basics", "Strategies", "Risk Management"])
    
    with tab1:
        st.markdown("""
        ### Investment Basics
        
        **What is investing?**
        Investing means putting your money to work to potentially earn more money over time. Instead of keeping cash in a savings account, you buy assets like stocks, bonds, or funds.
        
        **Key Concepts:**
        - **Stocks**: Ownership shares in companies
        - **Bonds**: Loans to companies or governments
        - **ETFs**: Baskets of stocks or bonds
        - **Diversification**: Don't put all eggs in one basket
        - **Risk vs. Return**: Higher potential returns usually mean higher risk
        """)
    
    with tab2:
        st.markdown("""
        ### Common Investment Strategies
        
        **Conservative (Low Risk)**
        - Focus on bonds and dividend stocks
        - Steady, predictable returns
        - Good for short-term goals or risk-averse investors
        
        **Balanced (Medium Risk)**
        - Mix of stocks and bonds
        - Moderate growth with some stability
        - Suitable for most long-term investors
        
        **Aggressive (High Risk)**
        - Mostly stocks, especially growth stocks
        - Higher potential returns but more volatility
        - Best for long-term goals and risk-tolerant investors
        """)
    
    with tab3:
        st.markdown("""
        ### Managing Investment Risk
        
        **Types of Risk:**
        - **Market Risk**: Overall market declines
        - **Company Risk**: Individual company problems
        - **Inflation Risk**: Money losing purchasing power
        
        **Risk Management Strategies:**
        - Diversify across different assets
        - Invest regularly (dollar-cost averaging)
        - Have a long-term perspective
        - Only invest what you can afford to lose
        - Review and rebalance periodically
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.9rem;">
    <p>LCS - Learn. Choose. Strategize. | Empowering beginners to invest with confidence</p>
    <p>⚠️ Disclaimer: This is for educational purposes only. Not financial advice.</p>
</div>
""", unsafe_allow_html=True)