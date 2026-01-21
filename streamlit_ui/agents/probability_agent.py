"""
Probability Lab Agent - Autonomous teacher for probabilistic thinking
Uses Claude API for intelligent decision making and feedback generation
"""

import streamlit as st
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import random
import uuid
from dataclasses import dataclass, asdict
import json

# Import tools
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from tools.kalshi_client import get_kalshi_client
from tools.metaculus_client import get_metaculus_client
from tools.calibration import CalibrationAnalyzer, Prediction
from config import config
# AI streaming import removed - using direct API calls

class ProbabilityAgent:
    """Autonomous agent for teaching probabilistic thinking"""
    
    def __init__(self):
        self.metaculus_client = get_metaculus_client()  # Primary source
        self.kalshi_client = get_kalshi_client()  # Fallback
        self.calibration_analyzer = CalibrationAnalyzer()
        
    def initialize_session_state(self):
        """Initialize or reset the probability lab session state"""
        if 'probability_lab' not in st.session_state:
            st.session_state.probability_lab = {
                'student_id': str(uuid.uuid4()),
                'skill_level': 'beginner',
                'interests': ['economics', 'technology'],
                'predictions': [],
                'calibration': {
                    'overall_brier': None,
                    'rolling_brier': [],
                    'by_domain': {},
                    'vs_market_baseline': None
                },
                'agent_state': {
                    'current_plan': 'Assess student level and present first prediction',
                    'session_goal': 'Build calibration through diverse predictions',
                    'predictions_this_session': 0,
                    'target_predictions': 10,
                    'next_action': 'present_prediction',
                    'domains_covered_this_session': [],
                    'current_market': None,
                    'feedback_history': []
                }
            }
    
    def decide_next_action(self, state: Dict) -> Dict[str, Any]:
        """
        Use LLM to decide what the agent should do next
        
        Returns:
            Action dictionary with type and parameters
        """
        # Analyze current state
        predictions_count = state['agent_state']['predictions_this_session']
        target = state['agent_state']['target_predictions']
        domains_covered = state['agent_state']['domains_covered_this_session']
        
        # Simple heuristic-based decision for now (can be enhanced with LLM)
        if predictions_count >= target:
            return {
                'type': 'review_session',
                'reason': 'Completed target predictions'
            }
        
        # Check for patterns that need explanation
        if len(state['predictions']) >= 3:
            biases = self.calibration_analyzer.identify_biases(state['predictions'])
            if biases and random.random() < 0.3:  # 30% chance to explain a bias
                bias_key = list(biases.keys())[0]
                return {
                    'type': 'explain_concept',
                    'concept': bias_key,
                    'explanation': biases[bias_key]
                }
        
        # Default: present next prediction
        return {
            'type': 'present_prediction',
            'reason': f'Continue practice ({predictions_count}/{target})'
        }
    
    def select_market(self, interests: List[str], skill_level: str,
                     domains_covered: List[str]) -> Optional[Dict]:
        """
        Select the best question for the student based on their profile
        Uses Metaculus as primary source, Kalshi as fallback

        Args:
            interests: Student's interest categories
            skill_level: beginner/intermediate/advanced
            domains_covered: Domains already covered this session

        Returns:
            Selected question/market dictionary or None
        """
        # Map interests to Metaculus topics
        topic_mapping = {
            'economics': 'economics',
            'technology': 'technology',
            'politics': 'politics',
            'science': 'science',
            'finance': 'finance',
            'business': 'business',
            'climate': 'science'
        }

        # Determine if politics should be included
        include_politics = 'politics' in [i.lower() for i in interests]

        # Get relevant topics
        relevant_topics = []
        for interest in interests:
            mapped = topic_mapping.get(interest.lower())
            if mapped and mapped not in relevant_topics:
                relevant_topics.append(mapped)

        # Try to rotate domains - prefer categories not recently covered
        preferred_topics = [
            topic for topic in relevant_topics
            if topic.title() not in domains_covered
        ] or relevant_topics

        # Try Metaculus first (primary source)
        all_questions = []

        if preferred_topics:
            # Fetch questions by topic
            for topic in preferred_topics[:3]:  # Limit API calls
                questions = self.metaculus_client.get_questions_by_topic(
                    topic,
                    limit=5,
                    include_politics=include_politics
                )
                all_questions.extend(questions)

        if not all_questions:
            # Fallback to LCS-relevant questions
            all_questions = self.metaculus_client.get_lcs_relevant_questions(
                limit=20,
                include_politics=include_politics
            )

        # If Metaculus fails, fallback to Kalshi
        if not all_questions:
            # Map interests to Kalshi categories
            kalshi_mapping = {
                'economics': ['Economics', 'Finance', 'Crypto'],
                'technology': ['Technology', 'Science'],
                'politics': ['Politics', 'Elections'],
                'sports': ['Sports', 'Football', 'Basketball'],
                'entertainment': ['Entertainment', 'Awards'],
                'climate': ['Climate', 'Weather']
            }

            kalshi_categories = []
            for interest in interests:
                kalshi_categories.extend(kalshi_mapping.get(interest.lower(), [interest]))

            for category in kalshi_categories[:3]:
                markets = self.kalshi_client.get_markets_by_category(category, limit=5)
                all_questions.extend(markets)

            if not all_questions:
                all_questions = self.kalshi_client.fetch_markets(status="open", limit=20)

        if not all_questions:
            return None

        # Filter and score questions based on criteria
        scored_questions = []
        for question in all_questions:
            score = 0

            # Prefer questions closing soon (within 7-90 days) for faster feedback
            close_time_str = question.get('close_time') or question.get('scheduled_close_time', '')
            try:
                if close_time_str:
                    close_time = datetime.fromisoformat(close_time_str.replace('Z', '+00:00'))
                    days_until_close = (close_time - datetime.now(close_time.tzinfo)).days
                    if 7 <= days_until_close <= 30:
                        score += 3
                    elif days_until_close <= 90:
                        score += 1
            except:
                pass

            # Skill level preferences based on number of predictions
            num_predictions = question.get('num_predictions', 0) or question.get('volume', 0)
            if skill_level == 'beginner':
                # Beginners: prefer questions with moderate activity
                if 50 <= num_predictions <= 500:
                    score += 2
            elif skill_level == 'advanced':
                # Advanced: prefer high activity (more efficient) questions
                if num_predictions > 500:
                    score += 2

            # Prefer questions with moderate probabilities (not too obvious)
            prob = question.get('community_prediction') or question.get('yes_bid', 50)
            if prob and 20 < prob < 80:
                score += 1  # Not too obvious

            # Bonus for questions not in covered domains
            category = question.get('category', 'General')
            if category not in domains_covered:
                score += 1

            scored_questions.append((question, score))

        # Sort by score and select
        scored_questions.sort(key=lambda x: x[1], reverse=True)

        if scored_questions:
            return scored_questions[0][0]
        return None
    
    def generate_feedback(self, student_prob: float, market: Dict,
                          reasoning: Optional[str], history: List[Prediction]) -> str:
        """
        Generate intelligent feedback on the student's prediction

        Args:
            student_prob: Student's probability estimate (0-100)
            market: Question/market dictionary (Metaculus or Kalshi)
            reasoning: Student's reasoning (optional)
            history: Previous predictions

        Returns:
            Feedback message
        """
        # Handle both Metaculus (community_prediction) and Kalshi (yes_bid) formats
        if market.get('community_prediction') is not None:
            market_prob = market['community_prediction'] / 100
        else:
            market_prob = market.get('yes_bid', 50) / 100
        student_prob_decimal = student_prob / 100
        diff = abs(student_prob_decimal - market_prob)
        
        # Build feedback components
        feedback_parts = []
        
        # 1. Direct comparison
        if diff < 0.05:
            feedback_parts.append(
                f"Your prediction ({student_prob:.0f}%) aligns closely with the market ({market_prob*100:.0f}%). "
                "This suggests you're thinking along similar lines to other predictors."
            )
        elif student_prob_decimal > market_prob:
            feedback_parts.append(
                f"You're {diff*100:.0f} percentage points more optimistic than the market. "
                f"The market is at {market_prob*100:.0f}%, while you predict {student_prob:.0f}%."
            )
        else:
            feedback_parts.append(
                f"You're {diff*100:.0f} percentage points more pessimistic than the market. "
                f"The market is at {market_prob*100:.0f}%, while you predict {student_prob:.0f}%."
            )
        
        # 2. Pattern recognition
        if len(history) >= 3:
            recent_diffs = [
                abs(p.student_probability - p.market_probability) 
                for p in history[-3:]
            ]
            avg_recent_diff = sum(recent_diffs) / len(recent_diffs)
            
            if avg_recent_diff > 0.15:
                feedback_parts.append(
                    "\n\nYou've been making bold predictions that differ significantly from the market. "
                    "This independent thinking is valuable, but remember to consider why the market might disagree."
                )
            elif avg_recent_diff < 0.05:
                feedback_parts.append(
                    "\n\nYour recent predictions have been very close to market prices. "
                    "Try forming your own view before checking the market consensus."
                )
        
        # 3. Calibration insight (if enough resolved predictions)
        resolved = [p for p in history if p.resolved]
        if len(resolved) >= 5:
            brier = self.calibration_analyzer.calculate_overall_brier(resolved)
            if brier < 0.15:
                feedback_parts.append(
                    f"\n\nYour calibration is excellent (Brier score: {brier:.3f}). Keep it up!"
                )
            elif brier > 0.25:
                feedback_parts.append(
                    f"\n\nThere's room to improve your calibration (Brier score: {brier:.3f}). "
                    "Consider whether you might be too confident in your predictions."
                )
        
        return " ".join(feedback_parts)
    
    def explain_concept(self, concept: str, skill_level: str) -> str:
        """
        Generate explanation of a cognitive bias or probability concept
        
        Args:
            concept: Concept to explain (e.g., 'overconfidence', 'base_rate')
            skill_level: Student's skill level
        
        Returns:
            Educational explanation
        """
        explanations = {
            'overconfidence': {
                'beginner': (
                    "**Overconfidence Bias**\n\n"
                    "We often feel more certain than we should be. When you predict 90% or 10%, "
                    "you're saying something is almost certain or almost impossible. "
                    "In reality, surprising things happen more often than we expect!\n\n"
                    "Try this: For your next few predictions, avoid going above 80% or below 20% "
                    "unless you have very strong evidence."
                ),
                'intermediate': (
                    "**Overconfidence Bias**\n\n"
                    "Research shows people consistently overestimate their prediction accuracy. "
                    "When experts say they're 90% confident, they're typically right only 70-80% of the time.\n\n"
                    "The market aggregates many opinions, which often makes it better calibrated than individuals. "
                    "Consider: what would have to be true for the market to be right and you to be wrong?"
                ),
                'advanced': (
                    "**Overconfidence & Calibration**\n\n"
                    "Your extreme predictions (>90% or <10%) should resolve correctly at those rates. "
                    "Track your calibration curve - if your 90% predictions come true only 70% of the time, "
                    "you're systematically overconfident.\n\n"
                    "Consider using reference classes and base rates to anchor your predictions "
                    "before adjusting for specific factors."
                )
            },
            'anchoring': {
                'beginner': (
                    "**Anchoring Bias**\n\n"
                    "The first number we see tends to influence our thinking, even when it shouldn't. "
                    "If you see the market is at 60%, you might predict 55% or 65% without really "
                    "thinking independently.\n\n"
                    "Try this: Make your prediction BEFORE looking at the market price, then compare."
                ),
                'intermediate': (
                    "**Anchoring to Market Prices**\n\n"
                    "Your predictions cluster very close to market prices. While markets are often wise, "
                    "you might have unique information or perspectives.\n\n"
                    "Practice: Write down your reasoning and initial estimate before seeing the market. "
                    "Only then check the market and decide if you want to adjust."
                ),
                'advanced': (
                    "**Market Efficiency vs. Edge**\n\n"
                    "Consistently predicting near market prices suggests either strong agreement with consensus "
                    "or anchoring bias. To develop an edge, you need to identify when you genuinely disagree "
                    "with the market based on analysis, not just noise.\n\n"
                    "Document your reasoning to distinguish between true disagreement and arbitrary deviation."
                )
            },
            'base_rate': {
                'beginner': (
                    "**Base Rate Thinking**\n\n"
                    "Before predicting a specific event, ask: 'How often does this type of thing usually happen?' "
                    "This is the base rate - your starting point.\n\n"
                    "Example: If only 20% of tech product launches happen on schedule historically, "
                    "start there and adjust based on specific factors."
                ),
                'intermediate': (
                    "**Base Rate Neglect**\n\n"
                    "We often ignore how common or rare something typically is (the base rate) "
                    "and focus too much on specific details of the current situation.\n\n"
                    "Strong prediction process:\n"
                    "1. Find the base rate\n"
                    "2. Identify what makes this case special\n"
                    "3. Adjust from the base rate accordingly"
                ),
                'advanced': (
                    "**Reference Class Forecasting**\n\n"
                    "Kahneman's 'outside view' starts with the reference class base rate. "
                    "Find the narrowest relevant reference class with sufficient data.\n\n"
                    "Then apply Bayesian updating: How much should specific evidence "
                    "move you from the prior (base rate)? Most people over-update on weak signals."
                )
            }
        }
        
        # Get explanation for concept and skill level
        concept_explanations = explanations.get(concept, {})
        explanation = concept_explanations.get(
            skill_level,
            concept_explanations.get('beginner', f"Let's work on understanding {concept}.")
        )
        
        return explanation
    
    def analyze_session(self, predictions: List[Prediction]) -> Dict:
        """
        Comprehensive analysis of a prediction session
        
        Args:
            predictions: List of predictions from the session
        
        Returns:
            Analysis dictionary with insights
        """
        session_predictions = predictions[-10:] if len(predictions) > 10 else predictions
        
        analysis = {
            'total_predictions': len(session_predictions),
            'domains_covered': list(set(p.category for p in session_predictions)),
            'average_confidence': None,
            'average_difference_from_market': None,
            'calibration_score': None,
            'identified_biases': {},
            'strengths': [],
            'areas_for_improvement': []
        }
        
        if session_predictions:
            # Calculate averages
            analysis['average_confidence'] = sum(
                p.student_probability for p in session_predictions
            ) / len(session_predictions) * 100
            
            analysis['average_difference_from_market'] = sum(
                abs(p.student_probability - p.market_probability) 
                for p in session_predictions
            ) / len(session_predictions) * 100
            
            # Get calibration if available
            resolved = [p for p in predictions if p.resolved]
            if resolved:
                analysis['calibration_score'] = self.calibration_analyzer.calculate_overall_brier(resolved)
            
            # Identify biases
            analysis['identified_biases'] = self.calibration_analyzer.identify_biases(session_predictions)
            
            # Identify strengths
            if analysis['average_difference_from_market'] > 10:
                analysis['strengths'].append("Independent thinking - you're not just following the crowd")
            
            if analysis['calibration_score'] and analysis['calibration_score'] < 0.2:
                analysis['strengths'].append("Good calibration - your confidence matches your accuracy")
            
            if len(analysis['domains_covered']) >= 3:
                analysis['strengths'].append("Diverse practice across multiple domains")
            
            # Areas for improvement
            if analysis['average_confidence'] > 70 or analysis['average_confidence'] < 30:
                analysis['areas_for_improvement'].append(
                    "Try making more moderate predictions - extreme confidence should be rare"
                )
            
            if analysis['identified_biases']:
                analysis['areas_for_improvement'].append(
                    f"Work on reducing {list(analysis['identified_biases'].keys())[0]}"
                )
        
        return analysis
    
    def store_prediction(self, market: Dict, student_prob: float,
                        reasoning: Optional[str] = None) -> Prediction:
        """
        Store a student's prediction in session state

        Args:
            market: Question/market dictionary (Metaculus or Kalshi)
            student_prob: Student's probability (0-100)
            reasoning: Optional reasoning text

        Returns:
            Prediction object
        """
        # Handle both Metaculus (community_prediction) and Kalshi (yes_bid) formats
        if market.get('community_prediction') is not None:
            market_prob = market['community_prediction'] / 100  # Already 0-100, convert to 0-1
        else:
            market_prob = market.get('yes_bid', 50) / 100

        # Get ticker/id - Metaculus uses 'ticker' field we added for compatibility
        market_ticker = market.get('ticker', f"metaculus-{market.get('id', 'unknown')}")

        # Get close time - handle both formats
        close_time_str = market.get('close_time') or market.get('scheduled_close_time', '')
        try:
            if close_time_str:
                market_close_time = datetime.fromisoformat(close_time_str.replace('Z', '+00:00'))
            else:
                market_close_time = datetime.now() + timedelta(days=30)  # Default fallback
        except:
            market_close_time = datetime.now() + timedelta(days=30)

        prediction = Prediction(
            id=str(uuid.uuid4()),
            market_ticker=market_ticker,
            market_title=market['title'],
            category=market.get('category', 'General'),
            student_probability=student_prob / 100,  # Convert to 0-1
            market_probability=market_prob,
            reasoning=reasoning,
            timestamp=datetime.now(),
            market_close_time=market_close_time,
            resolved=False,
            outcome=None,
            brier_score=None
        )

        # Add to session state
        st.session_state.probability_lab['predictions'].append(prediction)

        # Update session counters
        st.session_state.probability_lab['agent_state']['predictions_this_session'] += 1

        # Add domain to covered list
        if market.get('category'):
            domains = st.session_state.probability_lab['agent_state']['domains_covered_this_session']
            if market['category'] not in domains:
                domains.append(market['category'])

        return prediction
    
    def update_resolved_predictions(self):
        """Check for resolved predictions and update outcomes"""
        predictions = st.session_state.probability_lab.get('predictions', [])

        for pred in predictions:
            if not pred.resolved:
                # Check if this is a Metaculus or Kalshi prediction
                if pred.market_ticker.startswith('metaculus-'):
                    # Extract Metaculus question ID
                    try:
                        question_id = int(pred.market_ticker.replace('metaculus-', ''))
                        resolution = self.metaculus_client.check_resolution(question_id)
                    except (ValueError, TypeError):
                        continue
                else:
                    # Kalshi market
                    resolution = self.kalshi_client.check_resolution(pred.market_ticker)

                if resolution['resolved']:
                    pred.resolved = True
                    pred.outcome = resolution['outcome'] == 'yes'
                    pred.brier_score = self.calibration_analyzer.brier_score(
                        pred.student_probability,
                        pred.outcome
                    )

        # Update calibration metrics
        if predictions:
            resolved = [p for p in predictions if p.resolved]
            if resolved:
                st.session_state.probability_lab['calibration']['overall_brier'] = \
                    self.calibration_analyzer.calculate_overall_brier(resolved)

                st.session_state.probability_lab['calibration']['rolling_brier'] = \
                    self.calibration_analyzer.calculate_rolling_brier(resolved)

                st.session_state.probability_lab['calibration']['by_domain'] = \
                    self.calibration_analyzer.calculate_domain_performance(resolved)

                st.session_state.probability_lab['calibration']['vs_market_baseline'] = \
                    self.calibration_analyzer.compare_to_market(resolved)