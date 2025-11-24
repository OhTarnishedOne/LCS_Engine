"""
Strategy Display and AI Chat Page
Shows personalized strategies and allows Q&A
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

st.set_page_config(
    page_title="LCS - Your Strategies",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .strategy-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #4CAF50;
    }
    .confidence-high {
        color: #2E7D32;
        font-weight: bold;
    }
    .confidence-medium {
        color: #F57C00;
        font-weight: bold;
    }
    .confidence-low {
        color: #D32F2F;
        font-weight: bold;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .user-message {
        background: #E3F2FD;
        margin-left: 2rem;
    }
    .assistant-message {
        background: #F5F5F5;
        margin-right: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'strategies' not in st.session_state:
    st.session_state.strategies = []
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'selected_strategy' not in st.session_state:
    st.session_state.selected_strategy = None

def generate_strategies():
    """Generate personalized strategies based on user profile"""
    
    profile = st.session_state.get('user_profile', {})
    investor_type = profile.get('investor_type', 'Balanced')
    
    strategies = []
    
    if investor_type == "Conservative":
        strategies = [
            {
                "name": "Stable Income Portfolio",
                "description": "Focus on dividend-paying stocks and bonds for steady income",
                "allocation": {
                    "Bonds": 40,
                    "Dividend Stocks": 30,
                    "Large Cap": 20,
                    "Cash/Money Market": 10
                },
                "stocks": [
                    {"symbol": "JNJ", "name": "Johnson & Johnson", "confidence": 85, "reason": "Stable healthcare giant with 60+ years of dividend growth"},
                    {"symbol": "PG", "name": "Procter & Gamble", "confidence": 82, "reason": "Consumer staples leader with consistent dividends"},
                    {"symbol": "VZ", "name": "Verizon", "confidence": 78, "reason": "Telecom with high dividend yield and stable cash flow"},
                    {"symbol": "BND", "name": "Vanguard Bond ETF", "confidence": 90, "reason": "Diversified bond exposure for stability"}
                ],
                "expected_return": "4-6% annually",
                "risk_level": "Low"
            },
            {
                "name": "Capital Preservation Plus",
                "description": "Minimize risk while beating inflation",
                "allocation": {
                    "Treasury Bonds": 35,
                    "Corporate Bonds": 25,
                    "Utilities": 20,
                    "REITs": 10,
                    "Cash": 10
                },
                "stocks": [
                    {"symbol": "TLT", "name": "Treasury Bond ETF", "confidence": 92, "reason": "Government-backed securities for maximum safety"},
                    {"symbol": "NEE", "name": "NextEra Energy", "confidence": 80, "reason": "Leading renewable utility with growth potential"},
                    {"symbol": "O", "name": "Realty Income", "confidence": 85, "reason": "Monthly dividend REIT with stable tenants"},
                    {"symbol": "AGG", "name": "Core Bond ETF", "confidence": 88, "reason": "Broad bond market exposure"}
                ],
                "expected_return": "3-5% annually",
                "risk_level": "Very Low"
            }
        ]
    
    elif investor_type == "Aggressive":
        strategies = [
            {
                "name": "Growth Momentum Portfolio",
                "description": "High-growth tech and innovation stocks",
                "allocation": {
                    "Technology": 40,
                    "Growth Stocks": 30,
                    "Emerging Markets": 20,
                    "Small Cap": 10
                },
                "stocks": [
                    {"symbol": "NVDA", "name": "NVIDIA", "confidence": 88, "reason": "AI and datacenter growth leader"},
                    {"symbol": "TSLA", "name": "Tesla", "confidence": 75, "reason": "EV market leader with energy business potential"},
                    {"symbol": "NET", "name": "Cloudflare", "confidence": 72, "reason": "Edge computing and cybersecurity growth"},
                    {"symbol": "ARKK", "name": "ARK Innovation ETF", "confidence": 70, "reason": "Disruptive innovation exposure"}
                ],
                "expected_return": "12-20% annually (with high volatility)",
                "risk_level": "High"
            },
            {
                "name": "Tech Disruption Strategy",
                "description": "Focus on companies disrupting traditional industries",
                "allocation": {
                    "AI & Cloud": 35,
                    "Fintech": 25,
                    "Biotech": 20,
                    "Clean Energy": 20
                },
                "stocks": [
                    {"symbol": "MSFT", "name": "Microsoft", "confidence": 85, "reason": "Cloud and AI leader with Azure"},
                    {"symbol": "SQ", "name": "Block", "confidence": 73, "reason": "Fintech innovation in payments"},
                    {"symbol": "CRSP", "name": "CRISPR Therapeutics", "confidence": 68, "reason": "Gene editing breakthrough potential"},
                    {"symbol": "ENPH", "name": "Enphase Energy", "confidence": 71, "reason": "Solar technology innovator"}
                ],
                "expected_return": "15-25% annually (with high volatility)",
                "risk_level": "Very High"
            }
        ]
    
    else:  # Balanced
        strategies = [
            {
                "name": "Core & Satellite Portfolio",
                "description": "Balanced mix of stability and growth",
                "allocation": {
                    "Large Cap": 35,
                    "Bonds": 25,
                    "International": 20,
                    "Growth": 15,
                    "REITs": 5
                },
                "stocks": [
                    {"symbol": "SPY", "name": "S&P 500 ETF", "confidence": 90, "reason": "Broad market exposure to top US companies"},
                    {"symbol": "AAPL", "name": "Apple", "confidence": 85, "reason": "Tech leader with strong ecosystem and cash flow"},
                    {"symbol": "VXUS", "name": "International Stock ETF", "confidence": 82, "reason": "Global diversification outside US"},
                    {"symbol": "BND", "name": "Bond ETF", "confidence": 88, "reason": "Fixed income for stability"}
                ],
                "expected_return": "7-10% annually",
                "risk_level": "Moderate"
            },
            {
                "name": "Quality Growth Portfolio",
                "description": "High-quality companies with growth potential",
                "allocation": {
                    "Quality Growth": 40,
                    "Dividend Growth": 25,
                    "Bonds": 20,
                    "International": 15
                },
                "stocks": [
                    {"symbol": "GOOGL", "name": "Alphabet", "confidence": 84, "reason": "Search and cloud dominance with AI potential"},
                    {"symbol": "V", "name": "Visa", "confidence": 86, "reason": "Payment network with global growth"},
                    {"symbol": "HD", "name": "Home Depot", "confidence": 81, "reason": "Home improvement leader with pricing power"},
                    {"symbol": "SCHD", "name": "Dividend ETF", "confidence": 87, "reason": "Quality dividend growers"}
                ],
                "expected_return": "8-12% annually",
                "risk_level": "Moderate"
            }
        ]
    
    return strategies

# Main content
st.markdown("# 📊 Your Personalized Investment Strategies")

# Check if quiz is completed
if not st.session_state.get('quiz_completed', False):
    st.warning("Please complete the onboarding quiz first!")
    if st.button("Go to Quiz"):
        st.switch_page("pages/1_🎯_Onboarding.py")
else:
    # Generate strategies if not already done
    if not st.session_state.strategies:
        st.session_state.strategies = generate_strategies()
    
    # Display user profile summary
    profile = st.session_state.user_profile
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Investor Type", profile.get('investor_type', 'Balanced'))
    with col2:
        st.metric("Risk Tolerance", profile.get('risk_tolerance', 'Moderate'))
    with col3:
        st.metric("Timeline", profile.get('investment_timeline', 'Medium-term'))
    with col4:
        st.metric("Primary Goal", profile.get('primary_goal', 'Balanced'))
    
    st.markdown("---")
    
    # Strategy tabs
    tab1, tab2, tab3 = st.tabs(["📈 Your Strategies", "💬 AI Assistant", "📚 Learn More"])
    
    with tab1:
        st.markdown("## Based on your profile, here are your personalized strategies:")
        
        for idx, strategy in enumerate(st.session_state.strategies):
            with st.expander(f"**{strategy['name']}** - {strategy['risk_level']} Risk", expanded=(idx==0)):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown(f"**Description:** {strategy['description']}")
                    st.markdown(f"**Expected Return:** {strategy['expected_return']}")
                    st.markdown(f"**Risk Level:** {strategy['risk_level']}")
                    
                    # Stock recommendations
                    st.markdown("### 📊 Recommended Holdings:")
                    for stock in strategy['stocks']:
                        confidence_class = "high" if stock['confidence'] >= 80 else "medium" if stock['confidence'] >= 70 else "low"
                        st.markdown(f"""
                        **{stock['symbol']} - {stock['name']}**
                        <span class="confidence-{confidence_class}">Confidence: {stock['confidence']}%</span>
                        - {stock['reason']}
                        """, unsafe_allow_html=True)
                
                with col2:
                    # Pie chart for allocation
                    fig = px.pie(
                        values=list(strategy['allocation'].values()),
                        names=list(strategy['allocation'].keys()),
                        title="Portfolio Allocation",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"📋 Select This Strategy", key=f"select_{idx}"):
                        st.session_state.selected_strategy = strategy
                        st.success(f"Selected: {strategy['name']}")
                with col2:
                    if st.button(f"💬 Ask Questions", key=f"chat_{idx}"):
                        st.session_state.selected_strategy = strategy
                        st.info("Go to the AI Assistant tab to ask questions!")
                with col3:
                    if st.button(f"🎲 Test This Strategy", key=f"test_{idx}"):
                        st.session_state.selected_strategy = strategy
                        st.switch_page("pages/3_🎲_Paper_Trade.py")
    
    with tab2:
        st.markdown("## 💬 AI Investment Assistant")
        st.markdown("Ask me anything about your strategies, stocks, or investing in general!")
        
        # Display selected strategy context
        if st.session_state.selected_strategy:
            st.info(f"Currently discussing: **{st.session_state.selected_strategy['name']}**")
        
        # Chat interface
        chat_container = st.container()
        
        # Display chat history
        for message in st.session_state.chat_messages:
            if message["role"] == "user":
                st.markdown(f'<div class="chat-message user-message">👤 {message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message assistant-message">🤖 {message["content"]}</div>', unsafe_allow_html=True)
        
        # Chat input
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("Type your question here...", placeholder="e.g., Why did you recommend Apple stock?")
            col1, col2 = st.columns([4, 1])
            with col2:
                submitted = st.form_submit_button("Send", type="primary", use_container_width=True)
            
            if submitted and user_input:
                # Add user message
                st.session_state.chat_messages.append({"role": "user", "content": user_input})
                
                # Generate AI response (mock for now - would integrate with OpenAI)
                ai_response = generate_ai_response(user_input)
                st.session_state.chat_messages.append({"role": "assistant", "content": ai_response})
                
                st.rerun()
        
        # Sample questions
        st.markdown("### 💡 Sample Questions:")
        sample_questions = [
            "Why is this strategy good for my risk tolerance?",
            "What's the difference between growth and dividend stocks?",
            "How often should I rebalance my portfolio?",
            "What happens if the market crashes?"
        ]
        
        cols = st.columns(2)
        for idx, question in enumerate(sample_questions):
            with cols[idx % 2]:
                if st.button(question, key=f"sample_{idx}", use_container_width=True):
                    st.session_state.chat_messages.append({"role": "user", "content": question})
                    ai_response = generate_ai_response(question)
                    st.session_state.chat_messages.append({"role": "assistant", "content": ai_response})
                    st.rerun()
    
    with tab3:
        st.markdown("## 📚 Understanding Your Strategies")
        
        # Educational content about the strategies
        st.markdown("""
        ### Key Terms Explained
        
        **Portfolio Allocation:** How your money is divided among different types of investments.
        
        **Confidence Score:** Our AI's confidence in each stock recommendation based on:
        - Historical performance
        - Company fundamentals
        - Market conditions
        - Alignment with your goals
        
        **Expected Return:** The average annual gain you might expect (not guaranteed).
        
        **Risk Level:** How much the value might fluctuate:
        - **Low:** Stable, minimal fluctuations
        - **Moderate:** Some ups and downs
        - **High:** Significant volatility possible
        """)
        
        # Strategy comparison
        if len(st.session_state.strategies) > 1:
            st.markdown("### Strategy Comparison")
            comparison_data = []
            for strategy in st.session_state.strategies:
                comparison_data.append({
                    "Strategy": strategy['name'],
                    "Risk Level": strategy['risk_level'],
                    "Expected Return": strategy['expected_return'],
                    "Best For": get_strategy_best_for(strategy['risk_level'])
                })
            
            df = pd.DataFrame(comparison_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

def generate_ai_response(question):
    """Generate AI response (mock implementation - would use OpenAI in production)"""
    
    # Mock responses based on common questions
    responses = {
        "risk": "Based on your quiz results, you indicated you'd hold or buy more during market downturns. This shows you can handle moderate volatility, which is why we've suggested strategies with balanced risk-reward profiles.",
        "apple": "Apple is recommended because it's a financially strong company with consistent revenue growth, a loyal customer base, and strong cash generation. It fits well in a balanced portfolio.",
        "dividend": "Growth stocks reinvest profits to expand the business, offering potential for price appreciation. Dividend stocks pay out profits to shareholders regularly, providing income. Your portfolio includes both for balance.",
        "rebalance": "For beginners, reviewing your portfolio quarterly and rebalancing annually is typically sufficient. This helps maintain your target allocation without over-trading.",
        "crash": "Market crashes are temporary. Historical data shows that diversified portfolios recover over time. Your strategy is designed for your timeline, so short-term volatility shouldn't affect your long-term goals."
    }
    
    # Simple keyword matching (would use OpenAI in production)
    question_lower = question.lower()
    for key, response in responses.items():
        if key in question_lower:
            return response
    
    # Default response
    return "Great question! In a real implementation, I would use AI to provide a detailed, personalized answer based on your profile and selected strategy. For now, I recommend discussing this with a financial advisor or doing additional research on reputable investment education sites."

def get_strategy_best_for(risk_level):
    """Get description of who strategy is best for"""
    mapping = {
        "Very Low": "Capital preservation, near retirement",
        "Low": "Conservative investors, short-term goals",
        "Moderate": "Balanced growth, medium-term goals",
        "High": "Growth-focused, long-term investors",
        "Very High": "Risk-tolerant, young investors"
    }
    return mapping.get(risk_level, "Varied investors")