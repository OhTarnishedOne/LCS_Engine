"""
Calibration scoring utilities for probability predictions
Implements Brier score and calibration analysis
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

@dataclass
class Prediction:
    """Data class for a single prediction"""
    id: str
    market_ticker: str
    market_title: str
    category: str
    student_probability: float  # 0-1
    market_probability: float   # 0-1
    reasoning: Optional[str]
    timestamp: datetime
    market_close_time: datetime
    resolved: bool
    outcome: Optional[bool]  # True=YES, False=NO, None=pending
    brier_score: Optional[float]

class CalibrationAnalyzer:
    """Analyzes prediction calibration and scoring"""
    
    @staticmethod
    def brier_score(probability: float, outcome: bool) -> float:
        """
        Calculate Brier score for a single prediction
        
        Args:
            probability: Predicted probability (0-1)
            outcome: Actual outcome (True=YES, False=NO)
        
        Returns:
            Brier score (0=perfect, 1=worst)
        """
        outcome_val = 1.0 if outcome else 0.0
        return (probability - outcome_val) ** 2
    
    @staticmethod
    def calculate_calibration_curve(predictions: List[Prediction]) -> Dict:
        """
        Calculate calibration curve data
        Groups predictions by probability decile and compares to actual outcomes
        
        Args:
            predictions: List of resolved predictions
        
        Returns:
            Dictionary with calibration curve data
        """
        # Filter only resolved predictions
        resolved = [p for p in predictions if p.resolved and p.outcome is not None]
        
        if not resolved:
            return {
                "bins": [],
                "predicted": [],
                "actual": [],
                "counts": [],
                "perfect_calibration": []
            }
        
        # Create probability bins (0-10%, 10-20%, etc.)
        bins = np.linspace(0, 1, 11)
        bin_labels = [f"{int(bins[i]*100)}-{int(bins[i+1]*100)}%" for i in range(len(bins)-1)]
        
        calibration_data = {
            "bins": bin_labels,
            "predicted": [],
            "actual": [],
            "counts": [],
            "perfect_calibration": []
        }
        
        # Group predictions by bin
        for i in range(len(bins) - 1):
            bin_min, bin_max = bins[i], bins[i+1]
            
            # Find predictions in this bin
            bin_predictions = [
                p for p in resolved 
                if bin_min <= p.student_probability < bin_max or 
                   (i == len(bins) - 2 and p.student_probability == 1.0)  # Include 1.0 in last bin
            ]
            
            if bin_predictions:
                # Average predicted probability
                avg_predicted = np.mean([p.student_probability for p in bin_predictions])
                # Actual resolution rate
                actual_rate = np.mean([1 if p.outcome else 0 for p in bin_predictions])
                
                calibration_data["predicted"].append(avg_predicted * 100)
                calibration_data["actual"].append(actual_rate * 100)
                calibration_data["counts"].append(len(bin_predictions))
            else:
                calibration_data["predicted"].append((bin_min + bin_max) / 2 * 100)
                calibration_data["actual"].append(0)
                calibration_data["counts"].append(0)
            
            # Perfect calibration line
            calibration_data["perfect_calibration"].append((bin_min + bin_max) / 2 * 100)
        
        return calibration_data
    
    @staticmethod
    def calculate_overall_brier(predictions: List[Prediction]) -> float:
        """
        Calculate overall Brier score across all resolved predictions
        
        Args:
            predictions: List of predictions
        
        Returns:
            Average Brier score
        """
        resolved = [p for p in predictions if p.resolved and p.outcome is not None]
        
        if not resolved:
            return 0.0
        
        scores = [
            CalibrationAnalyzer.brier_score(p.student_probability, p.outcome)
            for p in resolved
        ]
        
        return np.mean(scores) if scores else 0.0
    
    @staticmethod
    def calculate_rolling_brier(predictions: List[Prediction], window: int = 20) -> List[float]:
        """
        Calculate rolling Brier score over last N predictions
        
        Args:
            predictions: List of predictions (sorted by timestamp)
            window: Rolling window size
        
        Returns:
            List of rolling Brier scores
        """
        resolved = [p for p in predictions if p.resolved and p.outcome is not None]
        
        if len(resolved) < window:
            # Not enough data for rolling window
            if resolved:
                return [CalibrationAnalyzer.calculate_overall_brier(resolved)]
            return []
        
        rolling_scores = []
        for i in range(window - 1, len(resolved)):
            window_predictions = resolved[i - window + 1:i + 1]
            score = CalibrationAnalyzer.calculate_overall_brier(window_predictions)
            rolling_scores.append(score)
        
        return rolling_scores
    
    @staticmethod
    def calculate_domain_performance(predictions: List[Prediction]) -> Dict[str, float]:
        """
        Calculate Brier scores by category/domain
        
        Args:
            predictions: List of predictions
        
        Returns:
            Dictionary mapping categories to Brier scores
        """
        resolved = [p for p in predictions if p.resolved and p.outcome is not None]
        
        if not resolved:
            return {}
        
        # Group by category
        categories = {}
        for pred in resolved:
            cat = pred.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(pred)
        
        # Calculate score for each category
        domain_scores = {}
        for cat, cat_predictions in categories.items():
            if cat_predictions:
                domain_scores[cat] = CalibrationAnalyzer.calculate_overall_brier(cat_predictions)
        
        return domain_scores
    
    @staticmethod
    def compare_to_market(predictions: List[Prediction]) -> Dict:
        """
        Compare student performance to market baseline
        
        Args:
            predictions: List of predictions
        
        Returns:
            Dictionary with comparison metrics
        """
        resolved = [p for p in predictions if p.resolved and p.outcome is not None]
        
        if not resolved:
            return {
                "student_brier": None,
                "market_brier": None,
                "relative_performance": None,
                "better_than_market_pct": None
            }
        
        # Calculate student Brier
        student_scores = [
            CalibrationAnalyzer.brier_score(p.student_probability, p.outcome)
            for p in resolved
        ]
        student_brier = np.mean(student_scores)
        
        # Calculate market Brier (if market prices were used)
        market_scores = [
            CalibrationAnalyzer.brier_score(p.market_probability, p.outcome)
            for p in resolved
        ]
        market_brier = np.mean(market_scores)
        
        # Count predictions where student beat market
        better_count = sum(
            1 for i in range(len(resolved))
            if student_scores[i] < market_scores[i]
        )
        
        return {
            "student_brier": student_brier,
            "market_brier": market_brier,
            "relative_performance": market_brier - student_brier,  # Positive = student better
            "better_than_market_pct": (better_count / len(resolved)) * 100 if resolved else 0
        }
    
    @staticmethod
    def identify_biases(predictions: List[Prediction]) -> Dict[str, str]:
        """
        Identify potential cognitive biases in predictions
        
        Args:
            predictions: List of predictions
        
        Returns:
            Dictionary of identified biases with explanations
        """
        biases = {}
        
        if len(predictions) < 5:
            return {"insufficient_data": "Need at least 5 predictions to identify patterns"}
        
        # Check for overconfidence (too many extreme predictions)
        extreme_predictions = [
            p for p in predictions 
            if p.student_probability > 0.9 or p.student_probability < 0.1
        ]
        
        if len(extreme_predictions) / len(predictions) > 0.3:
            biases["overconfidence"] = (
                "You frequently make very confident predictions (>90% or <10%). "
                "Consider that most real-world events have more uncertainty than we think."
            )
        
        # Check for anchoring (predictions too close to market)
        if predictions:
            diffs = [abs(p.student_probability - p.market_probability) for p in predictions]
            avg_diff = np.mean(diffs)
            
            if avg_diff < 0.05:  # Average difference less than 5%
                biases["anchoring"] = (
                    "Your predictions are very close to market prices. "
                    "Try forming independent judgments before looking at the market."
                )
            
        # Check for systematic over/under confidence
        resolved = [p for p in predictions if p.resolved and p.outcome is not None]
        if len(resolved) >= 5:
            # Compare predicted probabilities to actual outcomes
            overconfident_correct = [
                p for p in resolved 
                if p.student_probability > 0.7 and p.outcome
            ]
            overconfident_wrong = [
                p for p in resolved 
                if p.student_probability > 0.7 and not p.outcome
            ]
            
            if len(overconfident_wrong) > len(overconfident_correct):
                biases["systematic_overconfidence"] = (
                    "When you're confident (>70%), you're wrong more often than right. "
                    "Consider being more conservative with high-confidence predictions."
                )
        
        # Check for base rate neglect
        # (Would need historical base rates for proper analysis)
        
        return biases
    
    @staticmethod
    def generate_feedback(prediction: Prediction, history: List[Prediction]) -> str:
        """
        Generate contextual feedback for a prediction
        
        Args:
            prediction: The current prediction
            history: Previous predictions
        
        Returns:
            Feedback message
        """
        diff = abs(prediction.student_probability - prediction.market_probability)
        
        feedback = []
        
        # Compare to market
        if diff < 0.05:
            feedback.append(f"Your prediction ({prediction.student_probability*100:.0f}%) is very close to the market ({prediction.market_probability*100:.0f}%).")
        elif prediction.student_probability > prediction.market_probability:
            feedback.append(f"You're {diff*100:.0f} percentage points more confident than the market.")
        else:
            feedback.append(f"You're {diff*100:.0f} percentage points less confident than the market.")
        
        # Check for patterns
        if len(history) >= 5:
            recent = history[-5:]
            recent_diffs = [abs(p.student_probability - p.market_probability) for p in recent]
            
            if all(p.student_probability > p.market_probability for p in recent):
                feedback.append("You've been consistently more optimistic than the market recently.")
            elif all(p.student_probability < p.market_probability for p in recent):
                feedback.append("You've been consistently more pessimistic than the market recently.")
        
        # Category-specific feedback
        category_predictions = [p for p in history if p.category == prediction.category]
        if len(category_predictions) >= 3:
            cat_brier = CalibrationAnalyzer.calculate_overall_brier(
                [p for p in category_predictions if p.resolved]
            )
            if cat_brier > 0:
                if cat_brier < 0.15:
                    feedback.append(f"You're well-calibrated in {prediction.category} questions!")
                elif cat_brier > 0.25:
                    feedback.append(f"Consider being more careful with {prediction.category} predictions.")
        
        return " ".join(feedback)