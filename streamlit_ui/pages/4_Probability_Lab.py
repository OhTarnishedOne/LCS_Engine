"""
Probability Lab - Learn probabilistic thinking through prediction markets
Interactive module for calibration training using Kalshi markets
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import sys
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import dependencies
from agents.probability_agent import ProbabilityAgent
from tools.metaculus_client import get_metaculus_client
from tools.kalshi_client import get_kalshi_client
from tools.calibration import CalibrationAnalyzer, Prediction
from session_utils import save_session, display_session_info

# Page configuration
st.set_page_config(
    page_title="LCS - Probability Lab",
    page_icon="🎲",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .prediction-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #4CAF50;
    }
    .feedback-positive {
        background: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    .feedback-neutral {
        background: #d1ecf1;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #17a2b8;
    }
    .feedback-improve {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize agent
agent = ProbabilityAgent()
agent.initialize_session_state()

# Display session info
display_session_info()

# Header
st.markdown("# 🎲 Probability Lab")
st.markdown("### Learn to calibrate your predictions using real prediction markets")

# Check for resolved predictions
with st.spinner("Checking for resolved predictions..."):
    agent.update_resolved_predictions()

# Sidebar configuration
with st.sidebar:
    st.markdown("## ⚙️ Lab Settings")
    
    # Skill level selector
    skill_level = st.selectbox(
        "Your Experience Level",
        ["beginner", "intermediate", "advanced"],
        index=["beginner", "intermediate", "advanced"].index(
            st.session_state.probability_lab.get('skill_level', 'beginner')
        )
    )
    st.session_state.probability_lab['skill_level'] = skill_level
    
    # Interest categories
    st.markdown("### 📚 Topics of Interest")
    interests = []
    
    if st.checkbox("Economics & Finance", value=True):
        interests.append("economics")
    if st.checkbox("Technology & Science", value=True):
        interests.append("technology")
    if st.checkbox("Politics & Policy"):
        interests.append("politics")
    if st.checkbox("Sports"):
        interests.append("sports")
    if st.checkbox("Entertainment"):
        interests.append("entertainment")
    if st.checkbox("Climate & Environment"):
        interests.append("climate")
    
    st.session_state.probability_lab['interests'] = interests
    
    # Session configuration
    st.markdown("### 🎯 Session Settings")
    target_predictions = st.slider(
        "Predictions per session",
        min_value=5,
        max_value=20,
        value=st.session_state.probability_lab['agent_state']['target_predictions'],
        step=5
    )
    st.session_state.probability_lab['agent_state']['target_predictions'] = target_predictions
    
    # Progress
    st.markdown("### 📊 Session Progress")
    current = st.session_state.probability_lab['agent_state']['predictions_this_session']
    target = st.session_state.probability_lab['agent_state']['target_predictions']
    st.progress(current / target if target > 0 else 0)
    st.write(f"{current} / {target} predictions")
    
    # Reset session button
    if st.button("🔄 New Session", type="secondary"):
        st.session_state.probability_lab['agent_state']['predictions_this_session'] = 0
        st.session_state.probability_lab['agent_state']['domains_covered_this_session'] = []
        st.session_state.probability_lab['agent_state']['current_market'] = None
        st.rerun()

# Main content area with tabs
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Practice", "📊 Dashboard", "📈 Analysis", "📚 Learn"])

# Tab 1: Practice Mode
with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Current Prediction Exercise")
        
        # Get next action from agent
        state = st.session_state.probability_lab
        action = agent.decide_next_action(state)
        
        if action['type'] == 'present_prediction':
            # Get or select a market
            current_market = state['agent_state'].get('current_market')
            
            if not current_market or st.button("🔄 Get New Question"):
                with st.spinner("Finding the perfect prediction question for you..."):
                    current_market = agent.select_market(
                        interests=state['interests'],
                        skill_level=state['skill_level'],
                        domains_covered=state['agent_state']['domains_covered_this_session']
                    )
                    
                    if current_market:
                        state['agent_state']['current_market'] = current_market
                    else:
                        st.error("Could not fetch prediction markets. Please check your connection and try again.")
            
            if current_market:
                # Determine source (Metaculus or Kalshi) and format accordingly
                is_metaculus = current_market.get('url') is not None

                # Get close time - handle both formats
                close_time = current_market.get('close_time') or current_market.get('scheduled_close_time', 'Unknown')
                if close_time and close_time != 'Unknown':
                    try:
                        close_dt = datetime.fromisoformat(close_time.replace('Z', '+00:00'))
                        close_time = close_dt.strftime('%Y-%m-%d')
                    except:
                        pass

                # Get activity metric
                if is_metaculus:
                    activity = f"{current_market.get('num_predictions', 0):,} predictions"
                    source_badge = "Metaculus"
                else:
                    activity = f"${current_market.get('volume', 0):,} volume"
                    source_badge = "Kalshi"

                # Get subtitle/description
                subtitle = current_market.get('subtitle', '') or current_market.get('description', '')
                if subtitle and len(subtitle) > 200:
                    subtitle = subtitle[:200] + '...'

                # Display the prediction question
                st.markdown(f"""
                <div class="prediction-card">
                    <span style="background: #4CAF50; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{source_badge}</span>
                    <h4 style="margin-top: 10px;">{current_market['title']}</h4>
                    <p><em>{subtitle}</em></p>
                    <p><strong>Category:</strong> {current_market.get('category', 'General')}</p>
                    <p><strong>Closes:</strong> {close_time}</p>
                    <p><strong>Activity:</strong> {activity}</p>
                </div>
                """, unsafe_allow_html=True)

                # Add link to original question for Metaculus
                if is_metaculus and current_market.get('url'):
                    st.markdown(f"[View on Metaculus]({current_market['url']})")
                
                # Prediction input
                st.markdown("### Your Prediction")
                
                # Probability slider
                student_prob = st.slider(
                    "What's the probability this will happen?",
                    min_value=0,
                    max_value=100,
                    value=50,
                    step=1,
                    help="0% = definitely won't happen, 100% = definitely will happen"
                )
                
                # Reasoning text area
                reasoning = st.text_area(
                    "Explain your reasoning (optional)",
                    placeholder="What factors influenced your prediction?",
                    height=100
                )
                
                # Submit button
                if st.button("Submit Prediction", type="primary"):
                    # Store prediction
                    prediction = agent.store_prediction(
                        market=current_market,
                        student_prob=student_prob,
                        reasoning=reasoning
                    )
                    
                    # Generate and display feedback
                    feedback = agent.generate_feedback(
                        student_prob=student_prob,
                        market=current_market,
                        reasoning=reasoning,
                        history=state['predictions'][:-1]  # Exclude just-added prediction
                    )
                    
                    st.markdown("### Feedback")
                    st.info(feedback)
                    
                    # Show market comparison - handle both Metaculus and Kalshi formats
                    if current_market.get('community_prediction') is not None:
                        market_prob = current_market['community_prediction']
                    else:
                        market_prob = current_market.get('yes_bid', 50)
                    col1_inner, col2_inner = st.columns(2)
                    
                    with col1_inner:
                        st.metric("Your Prediction", f"{student_prob}%")
                    with col2_inner:
                        consensus_label = "Community Forecast" if is_metaculus else "Market Consensus"
                        st.metric(consensus_label, f"{market_prob:.0f}%")
                    
                    # Clear current market for next prediction
                    state['agent_state']['current_market'] = None
                    
                    # Save session
                    save_session()
                    
                    # Pause before next question
                    time.sleep(2)
                    st.rerun()
        
        elif action['type'] == 'explain_concept':
            # Display concept explanation
            st.markdown("### 💡 Learning Moment")
            explanation = agent.explain_concept(
                concept=action['concept'],
                skill_level=state['skill_level']
            )
            st.markdown(explanation)
            
            if st.button("Continue to Next Prediction"):
                state['agent_state']['next_action'] = 'present_prediction'
                st.rerun()
        
        elif action['type'] == 'review_session':
            # Session review
            st.markdown("### 🎉 Session Complete!")
            
            analysis = agent.analyze_session(state['predictions'])
            
            # Display session summary
            col1_review, col2_review, col3_review = st.columns(3)
            
            with col1_review:
                st.metric("Predictions Made", analysis['total_predictions'])
            with col2_review:
                if analysis['average_confidence']:
                    st.metric("Avg Confidence", f"{analysis['average_confidence']:.0f}%")
            with col3_review:
                if analysis['calibration_score']:
                    st.metric("Calibration Score", f"{analysis['calibration_score']:.3f}")
            
            # Strengths and improvements
            if analysis['strengths']:
                st.markdown("### ✅ Strengths")
                for strength in analysis['strengths']:
                    st.success(strength)
            
            if analysis['areas_for_improvement']:
                st.markdown("### 📈 Areas for Growth")
                for area in analysis['areas_for_improvement']:
                    st.info(area)
            
            # Reset for new session
            if st.button("Start New Session", type="primary"):
                state['agent_state']['predictions_this_session'] = 0
                state['agent_state']['domains_covered_this_session'] = []
                state['agent_state']['next_action'] = 'present_prediction'
                st.rerun()
    
    with col2:
        # Quick stats panel
        st.markdown("### 📊 Your Stats")
        
        predictions = state.get('predictions', [])
        if predictions:
            resolved = [p for p in predictions if p.resolved]
            
            st.metric("Total Predictions", len(predictions))
            st.metric("Resolved", len(resolved))
            
            if resolved:
                calibration = state.get('calibration', {})
                brier = calibration.get('overall_brier')
                if brier:
                    st.metric("Brier Score", f"{brier:.3f}", 
                             help="Lower is better (0=perfect, 1=worst)")
                
                vs_market = calibration.get('vs_market_baseline', {})
                if vs_market.get('better_than_market_pct'):
                    st.metric("Beat Market", 
                             f"{vs_market['better_than_market_pct']:.0f}%",
                             help="% of predictions better than market")

# Tab 2: Dashboard
with tab2:
    st.markdown("### 📊 Your Prediction Dashboard")
    
    predictions = st.session_state.probability_lab.get('predictions', [])
    
    if not predictions:
        st.info("No predictions yet. Start practicing to see your dashboard!")
    else:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        resolved = [p for p in predictions if p.resolved]
        calibration = st.session_state.probability_lab.get('calibration', {})
        
        with col1:
            st.metric("Total Predictions", len(predictions))
        with col2:
            st.metric("Resolved", len(resolved))
        with col3:
            if calibration.get('overall_brier') is not None:
                st.metric("Brier Score", f"{calibration['overall_brier']:.3f}")
        with col4:
            vs_market = calibration.get('vs_market_baseline', {})
            if vs_market.get('relative_performance') is not None:
                perf = vs_market['relative_performance']
                st.metric("vs Market", f"{perf:+.3f}", 
                         delta="Better" if perf > 0 else "Worse")
        
        # Calibration curve
        if len(resolved) >= 5:
            st.markdown("### Calibration Curve")
            
            cal_data = CalibrationAnalyzer.calculate_calibration_curve(resolved)
            
            if cal_data['predicted']:
                fig = go.Figure()
                
                # Actual calibration
                fig.add_trace(go.Bar(
                    x=cal_data['bins'],
                    y=cal_data['actual'],
                    name='Your Calibration',
                    marker_color='#4CAF50'
                ))
                
                # Perfect calibration line
                fig.add_trace(go.Scatter(
                    x=cal_data['bins'],
                    y=cal_data['perfect_calibration'],
                    mode='lines',
                    name='Perfect Calibration',
                    line=dict(color='gray', dash='dash')
                ))
                
                fig.update_layout(
                    title="How Well Calibrated Are Your Predictions?",
                    xaxis_title="Predicted Probability Range",
                    yaxis_title="Actual Outcome Rate (%)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Rolling Brier score
        if calibration.get('rolling_brier'):
            st.markdown("### Calibration Over Time")
            
            rolling = calibration['rolling_brier']
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=rolling,
                mode='lines+markers',
                name='Rolling Brier Score',
                line=dict(color='#4CAF50')
            ))
            
            # Add reference lines
            fig.add_hline(y=0.25, line_dash="dash", line_color="gray",
                         annotation_text="Good")
            fig.add_hline(y=0.15, line_dash="dash", line_color="green",
                         annotation_text="Excellent")
            
            fig.update_layout(
                title="Your Calibration Progress (20-prediction rolling window)",
                xaxis_title="Window",
                yaxis_title="Brier Score (lower is better)",
                height=350
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Performance by domain
        if calibration.get('by_domain'):
            st.markdown("### Performance by Category")
            
            domains = calibration['by_domain']
            if domains:
                df_domains = pd.DataFrame(
                    list(domains.items()),
                    columns=['Category', 'Brier Score']
                )
                
                fig = px.bar(df_domains, x='Category', y='Brier Score',
                           color='Brier Score',
                           color_continuous_scale='RdYlGn_r')
                
                fig.update_layout(
                    title="Which topics are you best at predicting?",
                    height=350
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Recent predictions table
        st.markdown("### Recent Predictions")
        
        recent = predictions[-10:] if len(predictions) > 10 else predictions
        recent.reverse()  # Show newest first
        
        table_data = []
        for pred in recent:
            table_data.append({
                'Question': pred.market_title[:50] + '...' if len(pred.market_title) > 50 else pred.market_title,
                'Your Prediction': f"{pred.student_probability*100:.0f}%",
                'Market': f"{pred.market_probability*100:.0f}%",
                'Difference': f"{abs(pred.student_probability - pred.market_probability)*100:.0f}%",
                'Category': pred.category,
                'Status': '✅ Resolved' if pred.resolved else '⏳ Pending',
                'Outcome': ('YES' if pred.outcome else 'NO') if pred.resolved else '-',
                'Brier': f"{pred.brier_score:.3f}" if pred.brier_score else '-'
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)

# Tab 3: Analysis
with tab3:
    st.markdown("### 📈 Deep Analysis")
    
    predictions = st.session_state.probability_lab.get('predictions', [])
    
    if len(predictions) < 5:
        st.info("Complete at least 5 predictions to unlock detailed analysis.")
    else:
        # Bias detection
        biases = CalibrationAnalyzer.identify_biases(predictions)
        
        if biases:
            st.markdown("### 🧠 Cognitive Patterns Detected")
            
            for bias_name, explanation in biases.items():
                if bias_name != 'insufficient_data':
                    st.warning(f"**{bias_name.replace('_', ' ').title()}**\n\n{explanation}")
        
        # Comparison to market
        calibration = st.session_state.probability_lab.get('calibration', {})
        vs_market = calibration.get('vs_market_baseline', {})
        
        if vs_market.get('student_brier') is not None:
            st.markdown("### You vs. The Market")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Brier score comparison
                fig = go.Figure(data=[
                    go.Bar(name='You', x=['Brier Score'], 
                          y=[vs_market['student_brier']],
                          marker_color='#4CAF50'),
                    go.Bar(name='Market', x=['Brier Score'], 
                          y=[vs_market['market_brier']],
                          marker_color='#FF6B6B')
                ])
                
                fig.update_layout(
                    title="Prediction Accuracy (lower is better)",
                    yaxis_title="Brier Score",
                    height=350
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Win rate
                win_pct = vs_market.get('better_than_market_pct', 0)
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=win_pct,
                    title={'text': "Beat Market Rate"},
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "#4CAF50" if win_pct > 50 else "#FF6B6B"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 100], 'color': "gray"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 50
                        }
                    }
                ))
                
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
        
        # Confidence distribution
        st.markdown("### Confidence Distribution")
        
        all_probs = [p.student_probability * 100 for p in predictions]
        
        fig = go.Figure(data=[go.Histogram(
            x=all_probs,
            nbinsx=20,
            marker_color='#4CAF50'
        )])
        
        fig.update_layout(
            title="How confident are your predictions?",
            xaxis_title="Prediction (%)",
            yaxis_title="Count",
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Tab 4: Learn
with tab4:
    st.markdown("### 📚 Probability & Prediction Education")
    
    learning_topic = st.selectbox(
        "Choose a topic to learn about:",
        ["Calibration Basics", "Cognitive Biases", "Base Rates", "Market Efficiency", "Brier Scoring"]
    )
    
    if learning_topic == "Calibration Basics":
        st.markdown("""
        #### What is Calibration?
        
        **Calibration** means your confidence matches your accuracy. If you say something has a 70% chance 
        of happening, and you make many such predictions, about 70% should come true.
        
        **Why it matters:**
        - Better decision making under uncertainty
        - More accurate risk assessment
        - Improved forecasting ability
        
        **How to improve:**
        1. **Track your predictions** - You can't improve what you don't measure
        2. **Get feedback** - See which predictions resolved and how
        3. **Identify patterns** - Notice if you're consistently over or under confident
        4. **Adjust** - Gradually calibrate your confidence levels
        
        **Perfect vs. Good Calibration:**
        - Perfect: Your 60% predictions happen exactly 60% of the time
        - Good: Your predictions are within 5-10% of the true rate
        - Most people start poorly calibrated but improve with practice!
        """)
    
    elif learning_topic == "Cognitive Biases":
        st.markdown("""
        #### Common Prediction Biases
        
        **1. Overconfidence Bias**
        - We think we know more than we do
        - Fix: Use base rates and be more moderate
        
        **2. Anchoring Bias**  
        - First number we see influences us too much
        - Fix: Make predictions before seeing others' estimates
        
        **3. Availability Heuristic**
        - Recent/memorable events seem more likely
        - Fix: Look at historical frequencies
        
        **4. Confirmation Bias**
        - We seek info that confirms our beliefs
        - Fix: Actively look for contradictory evidence
        
        **5. Base Rate Neglect**
        - Ignoring how common something typically is
        - Fix: Always start with the base rate
        """)
    
    elif learning_topic == "Base Rates":
        st.markdown("""
        #### The Power of Base Rates
        
        **What are base rates?**
        The historical frequency of an event - how often it typically happens.
        
        **Example:**
        - Question: "Will this startup succeed?"
        - Base rate: ~10% of startups succeed
        - Start at 10%, then adjust based on specific factors
        
        **Finding base rates:**
        1. Look for similar historical events
        2. Use the narrowest relevant category
        3. Ensure adequate sample size
        
        **Adjusting from base rates:**
        - Small adjustments for weak evidence
        - Larger adjustments for strong, unique evidence
        - Most people adjust too much!
        
        **Reference class forecasting:**
        1. Identify the reference class (similar cases)
        2. Find the base rate for that class
        3. Adjust moderately for unique factors
        """)
    
    elif learning_topic == "Market Efficiency":
        st.markdown("""
        #### Understanding Prediction Markets
        
        **What makes markets "wise"?**
        - Aggregate many opinions
        - Incentivize accuracy (real money)
        - Update continuously with new info
        
        **When markets might be wrong:**
        - Low liquidity (few traders)
        - Information asymmetry
        - Systematic biases
        - Manipulation
        
        **Your edge vs. the market:**
        - Unique information
        - Different interpretation
        - Longer time horizon
        - Domain expertise
        
        **When to trust markets:**
        - High volume/liquidity
        - Many participants
        - Clear resolution criteria
        - Efficient information flow
        """)
    
    elif learning_topic == "Brier Scoring":
        st.markdown("""
        #### Understanding Brier Scores
        
        **What is a Brier Score?**
        A measure of prediction accuracy ranging from 0 (perfect) to 1 (worst).
        
        **Formula:** `(prediction - outcome)²`
        - Prediction: Your probability (0-1)
        - Outcome: 1 if happened, 0 if didn't
        
        **Examples:**
        - You predict 80%, it happens: (0.8 - 1)² = 0.04 ✅
        - You predict 80%, it doesn't: (0.8 - 0)² = 0.64 ❌
        - You predict 50%, either way: (0.5 - 0/1)² = 0.25 🤷
        
        **Interpreting scores:**
        - < 0.1: Excellent
        - 0.1-0.2: Good
        - 0.2-0.25: Average
        - \> 0.25: Needs improvement
        
        **Why Brier Scores matter:**
        - Rewards both accuracy AND confidence
        - Penalizes overconfidence heavily
        - Single metric for prediction quality
        """)
    
    # Tips section
    st.markdown("---")
    st.markdown("### 💡 Quick Tips for Better Predictions")
    
    tips = [
        "Start with the base rate - how often does this typically happen?",
        "Write down your reasoning before seeing the market price",
        "Avoid extreme predictions (0-10% or 90-100%) unless you have strong evidence",
        "Track patterns in your predictions - are you consistently too optimistic or pessimistic?",
        "Consider what would have to be true for you to be wrong",
        "Update your beliefs gradually as new information arrives",
        "Practice across different domains to identify your strengths",
        "Remember: being wrong at 30% is better than being wrong at 90%!"
    ]
    
    for i, tip in enumerate(tips, 1):
        st.info(f"**Tip {i}:** {tip}")

# Save session state
save_session()