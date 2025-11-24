"""
Onboarding Quiz Page
Collects user preferences and risk profile
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path

st.set_page_config(
    page_title="LCS - Onboarding Quiz",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .question-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin: 2rem 0 1rem 0;
    }
    .progress-text {
        text-align: center;
        color: #666;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'quiz_step' not in st.session_state:
    st.session_state.quiz_step = 1
if 'quiz_answers' not in st.session_state:
    st.session_state.quiz_answers = {}

# Quiz questions
QUIZ_QUESTIONS = [
    {
        "id": "experience",
        "question": "How would you describe your investing experience?",
        "options": {
            "Beginner": "I'm completely new to investing",
            "Some Experience": "I've done some reading but haven't invested yet",
            "Intermediate": "I've made a few investments before",
            "Experienced": "I invest regularly and understand the basics"
        }
    },
    {
        "id": "goal",
        "question": "What's your primary investment goal?",
        "options": {
            "Growth": "Maximize returns, I can handle ups and downs",
            "Income": "Generate regular income from dividends",
            "Preservation": "Protect my money from inflation",
            "Balanced": "A mix of growth and stability"
        }
    },
    {
        "id": "timeline",
        "question": "When might you need this money?",
        "options": {
            "Short-term": "Within 1-2 years",
            "Medium-term": "3-5 years",
            "Long-term": "5-10 years",
            "Retirement": "More than 10 years"
        }
    },
    {
        "id": "risk_tolerance",
        "question": "If your investment dropped 20% in value tomorrow, what would you do?",
        "options": {
            "Sell Everything": "I'd panic and sell to prevent more losses",
            "Sell Some": "I'd sell some to reduce my exposure",
            "Hold": "I'd wait for it to recover",
            "Buy More": "I'd see it as a buying opportunity"
        }
    },
    {
        "id": "investment_amount",
        "question": "How much are you planning to invest initially?",
        "options": {
            "Small": "Less than $1,000",
            "Moderate": "$1,000 - $10,000",
            "Substantial": "$10,000 - $50,000",
            "Large": "More than $50,000"
        }
    }
]

# Main quiz interface
st.markdown("# 🎯 Investment Profile Quiz")
st.markdown("Let's get to know you better! This quick quiz will help us create personalized investment strategies just for you.")

# Progress bar
current_question = st.session_state.quiz_step
total_questions = len(QUIZ_QUESTIONS)
progress = current_question / total_questions

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(f'<p class="progress-text">Question {current_question} of {total_questions}</p>', unsafe_allow_html=True)
    st.progress(progress)

# Display current question
if current_question <= total_questions:
    question_data = QUIZ_QUESTIONS[current_question - 1]
    
    st.markdown(f'<h2 class="question-header">{question_data["question"]}</h2>', unsafe_allow_html=True)
    
    # Radio button options
    selected = st.radio(
        "Choose the option that best describes you:",
        options=list(question_data["options"].keys()),
        format_func=lambda x: f"{x}: {question_data['options'][x]}",
        key=f"q_{question_data['id']}"
    )
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if current_question > 1:
            if st.button("← Previous", use_container_width=True):
                st.session_state.quiz_step -= 1
                st.rerun()
    
    with col3:
        if current_question < total_questions:
            if st.button("Next →", type="primary", use_container_width=True):
                # Save answer
                st.session_state.quiz_answers[question_data["id"]] = selected
                st.session_state.quiz_step += 1
                st.rerun()
        else:
            if st.button("Complete Quiz ✓", type="primary", use_container_width=True):
                # Save final answer
                st.session_state.quiz_answers[question_data["id"]] = selected
                
                # Process results
                st.session_state.user_profile = process_quiz_results(st.session_state.quiz_answers)
                st.session_state.quiz_completed = True
                
                # Save to session file
                save_session_data()
                
                # Redirect to strategies page
                st.success("Quiz completed! Generating your personalized strategies...")
                st.balloons()
                st.switch_page("pages/2_📊_Strategies.py")

# Show quiz summary if completed
if st.session_state.quiz_completed:
    st.markdown("## ✅ Quiz Complete!")
    st.success("Your profile has been created. Click below to see your personalized strategies.")
    
    # Display profile summary
    with st.expander("Your Investment Profile"):
        for key, value in st.session_state.user_profile.items():
            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
    
    if st.button("View My Strategies →", type="primary", use_container_width=True):
        st.switch_page("pages/2_📊_Strategies.py")

def process_quiz_results(answers):
    """Process quiz answers into a user profile"""
    
    # Map answers to risk scores
    risk_mapping = {
        "Sell Everything": 1,
        "Sell Some": 2,
        "Hold": 3,
        "Buy More": 4
    }
    
    timeline_mapping = {
        "Short-term": 1,
        "Medium-term": 2,
        "Long-term": 3,
        "Retirement": 4
    }
    
    # Calculate risk score
    risk_score = risk_mapping.get(answers.get("risk_tolerance", "Hold"), 2)
    timeline_score = timeline_mapping.get(answers.get("timeline", "Medium-term"), 2)
    
    # Determine investor type
    if risk_score <= 2 and timeline_score <= 2:
        investor_type = "Conservative"
    elif risk_score >= 3 and timeline_score >= 3:
        investor_type = "Aggressive"
    else:
        investor_type = "Balanced"
    
    profile = {
        "investor_type": investor_type,
        "experience_level": answers.get("experience", "Beginner"),
        "primary_goal": answers.get("goal", "Balanced"),
        "investment_timeline": answers.get("timeline", "Medium-term"),
        "risk_tolerance": answers.get("risk_tolerance", "Hold"),
        "initial_investment": answers.get("investment_amount", "Moderate"),
        "risk_score": risk_score,
        "created_at": datetime.now().isoformat()
    }
    
    return profile

def save_session_data():
    """Save session data to a JSON file"""
    session_dir = Path(__file__).parent.parent.parent / "lcs_sessions"
    session_dir.mkdir(exist_ok=True)
    
    session_data = {
        "user_profile": st.session_state.user_profile,
        "quiz_answers": st.session_state.quiz_answers,
        "timestamp": datetime.now().isoformat()
    }
    
    filename = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(session_dir / filename, 'w') as f:
        json.dump(session_data, f, indent=2)
    
    st.session_state.session_file = str(session_dir / filename)