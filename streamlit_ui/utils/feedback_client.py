"""
Feedback Manager Client for Streamlit UI
Integrates with the MOAT feedback system
"""

import requests
from typing import Dict, Optional
import streamlit as st
from datetime import datetime

class FeedbackClient:
    """Client for interacting with the Feedback Manager API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def track_comprehension(self, user_id: str, strategy_id: str, 
                           confidence_before: int, confidence_after: int,
                           time_on_explanation: int, questions_asked: int = 0) -> Dict:
        """
        Track user comprehension of a strategy
        This is the MOAT's crown jewel - understanding what users actually learn
        """
        try:
            response = self.session.post(
                f"{self.base_url}/comprehension",
                json={
                    "user_id": user_id,
                    "strategy_id": strategy_id,
                    "confidence_before": confidence_before,
                    "confidence_after": confidence_after,
                    "time_on_explanation": time_on_explanation,
                    "questions_asked": questions_asked
                }
            )
            return response.json()
        except requests.exceptions.RequestException:
            return {"status": "offline", "message": "Feedback system not available"}
    
    def track_strategy_feedback(self, user_id: str, strategy_id: str, 
                               rating: int, action: str) -> Dict:
        """Track user feedback on a strategy"""
        try:
            response = self.session.post(
                f"{self.base_url}/feedback",
                json={
                    "user_id": user_id,
                    "strategy_id": strategy_id,
                    "rating": rating,
                    "action": action
                }
            )
            return response.json()
        except requests.exceptions.RequestException:
            return {"status": "offline"}
    
    def track_explanation_quality(self, user_id: str, strategy_id: str,
                                explanation_type: str, was_helpful: bool,
                                clarity_rating: int, improvement: Optional[str] = None) -> Dict:
        """Track which explanations actually teach"""
        try:
            response = self.session.post(
                f"{self.base_url}/explanation_feedback",
                json={
                    "user_id": user_id,
                    "strategy_id": strategy_id,
                    "explanation_type": explanation_type,
                    "was_helpful": was_helpful,
                    "clarity_rating": clarity_rating,
                    "suggested_improvement": improvement
                }
            )
            return response.json()
        except requests.exceptions.RequestException:
            return {"status": "offline"}
    
    def track_variant_choice(self, user_id: str, base_strategy_id: str,
                            variant_type: str, was_shown: bool, was_chosen: bool) -> Dict:
        """Track revealed preferences through variant testing"""
        try:
            response = self.session.post(
                f"{self.base_url}/variant",
                json={
                    "base_strategy_id": base_strategy_id,
                    "variant_type": variant_type,
                    "user_id": user_id,
                    "was_shown": was_shown,
                    "was_chosen": was_chosen
                }
            )
            return response.json()
        except requests.exceptions.RequestException:
            return {"status": "offline"}
    
    def get_moat_recommendations(self, user_id: str) -> Dict:
        """Get MOAT-driven recommendations based on comprehension + success"""
        try:
            response = self.session.get(f"{self.base_url}/recommend/{user_id}")
            return response.json()
        except requests.exceptions.RequestException:
            return {"recommendations": [], "reasoning": "Feedback system offline"}
    
    def get_moat_report(self) -> Dict:
        """Get competitive advantage analytics"""
        try:
            response = self.session.get(f"{self.base_url}/analytics/moat_report")
            return response.json()
        except requests.exceptions.RequestException:
            return {"moat_strength": "UNKNOWN", "message": "Feedback system offline"}

# Streamlit-specific helper functions
def add_comprehension_widget():
    """Add a comprehension check widget to Streamlit page"""
    with st.expander("📊 How confident are you with this strategy?"):
        col1, col2 = st.columns(2)
        with col1:
            confidence_before = st.slider(
                "Before explanation:", 
                min_value=1, max_value=10, value=5,
                help="How well do you understand this strategy?"
            )
        with col2:
            confidence_after = st.slider(
                "After explanation:", 
                min_value=1, max_value=10, value=7,
                help="How well do you understand now?"
            )
        
        questions = st.number_input(
            "How many questions do you have?",
            min_value=0, max_value=10, value=0
        )
        
        if st.button("Submit Comprehension Check"):
            return {
                "confidence_before": confidence_before,
                "confidence_after": confidence_after,
                "questions_asked": questions
            }
    return None

def add_explanation_feedback_widget():
    """Add explanation quality feedback widget"""
    with st.expander("💡 Was this explanation helpful?"):
        was_helpful = st.checkbox("This explanation helped me understand")
        clarity = st.slider("Clarity rating:", 1, 5, 3)
        improvement = st.text_area("How could we explain this better?")
        
        if st.button("Submit Feedback"):
            return {
                "was_helpful": was_helpful,
                "clarity_rating": clarity,
                "suggested_improvement": improvement
            }
    return None

def show_moat_metrics(client: FeedbackClient):
    """Display MOAT competitive advantage metrics"""
    report = client.get_moat_report()
    
    if report.get("moat_strength") != "UNKNOWN":
        st.markdown("### 🔒 Competitive Moat Strength")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Moat Strength", report["moat_strength"])
        with col2:
            st.metric("Avg Comprehension Lift", 
                     f"{report['key_metrics']['avg_comprehension_lift']}")
        with col3:
            st.metric("Success Rate", 
                     f"{report['key_metrics']['success_rate']}%")
        
        with st.expander("View Competitive Advantages"):
            for advantage in report["competitive_advantage"]:
                st.write(f"• {advantage}")
            st.info(f"Time to replicate: {report['time_to_replicate']}")

# Global client instance
feedback_client = FeedbackClient()