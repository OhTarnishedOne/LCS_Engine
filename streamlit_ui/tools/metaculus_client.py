"""
Metaculus API Client for fetching prediction question data
No authentication required for reading public questions
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import streamlit as st
import time


class MetaculusClient:
    """Client for interacting with Metaculus prediction questions API"""

    BASE_URL = "https://www.metaculus.com/api2/questions"

    # Topics relevant to LCS (economics, finance, tech, science)
    LCS_TOPICS = {
        'economics': ['economy', 'economic', 'gdp', 'inflation', 'recession', 'fed', 'interest rate'],
        'finance': ['stock', 'market', 'bitcoin', 'crypto', 'trading', 'investment', 'bank'],
        'technology': ['ai', 'artificial intelligence', 'tech', 'software', 'computer', 'digital', 'machine learning'],
        'science': ['research', 'study', 'scientific', 'climate', 'energy', 'space', 'physics'],
        'business': ['company', 'startup', 'acquisition', 'ipo', 'revenue', 'profit', 'ceo']
    }

    # Topics to exclude by default
    EXCLUDED_TOPICS = ['sports', 'entertainment', 'celebrity', 'movie', 'music', 'game', 'football', 'basketball']

    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_request_interval = 0.3  # 300ms between requests

    def _make_request(self, endpoint: str = "", params: Optional[Dict] = None) -> Optional[Dict]:
        """Make a rate-limited request to Metaculus API"""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        try:
            url = f"{self.BASE_URL}/{endpoint}" if endpoint else self.BASE_URL
            response = self.session.get(url, params=params, timeout=15)
            self.last_request_time = time.time()

            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Metaculus API request failed: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            st.error(f"Network error: {str(e)}")
            return None

    def _extract_community_prediction(self, question: Dict) -> Optional[float]:
        """
        Extract community prediction probability from question data

        Args:
            question: Raw question dictionary from API

        Returns:
            Probability as percentage (0-100) or None
        """
        try:
            # Metaculus API nests aggregations inside 'question' field
            question_data = question.get('question', {})
            if not question_data:
                # Fallback to top-level for backwards compatibility
                question_data = question

            aggregations = question_data.get('aggregations', {})

            # Try recency_weighted first, then unweighted, then single_aggregation
            for agg_type in ['recency_weighted', 'unweighted', 'single_aggregation']:
                if agg_type in aggregations:
                    agg_data = aggregations[agg_type]
                    if agg_data and agg_data.get('latest'):
                        latest = agg_data['latest']
                        centers = latest.get('centers', [])
                        if centers:
                            # centers[0] is the probability (0-1), convert to percentage
                            return centers[0] * 100

            return None
        except (KeyError, IndexError, TypeError):
            return None

    def _is_lcs_relevant(self, question: Dict, include_politics: bool = False) -> bool:
        """
        Check if question is relevant to LCS topics

        Args:
            question: Question dictionary (raw or processed)
            include_politics: Whether to include political questions

        Returns:
            True if question matches LCS topics
        """
        # Handle nested structure
        question_data = question.get('question', {})
        title = (question.get('title', '') or question_data.get('title', '')).lower()
        description = (question.get('description', '') or question_data.get('description', '') or '').lower()
        text = f"{title} {description}"

        # Check for excluded topics
        for excluded in self.EXCLUDED_TOPICS:
            if excluded in text:
                return False

        # Check for politics exclusion
        if not include_politics:
            politics_terms = ['election', 'president', 'congress', 'senate', 'political', 'vote', 'democrat', 'republican']
            for term in politics_terms:
                if term in text:
                    return False

        # Check for LCS-relevant topics
        for topic, keywords in self.LCS_TOPICS.items():
            for keyword in keywords:
                if keyword in text:
                    return True

        return False

    def _process_question(self, question: Dict) -> Dict:
        """
        Process raw question data into standardized format

        Args:
            question: Raw question from API

        Returns:
            Processed question dictionary
        """
        community_prob = self._extract_community_prediction(question)

        # Get data from nested 'question' field if present
        question_data = question.get('question', {})

        # Get title - try top-level first, then nested
        title = question.get("title", "") or question_data.get("title", "")

        # Get description - try top-level first, then nested
        description = question.get("description", "") or question_data.get("description", "")

        # Get close time - try top-level first, then nested
        close_time = (question.get("scheduled_close_time", "") or
                     question_data.get("scheduled_close_time", ""))

        # Get resolve time
        resolve_time = (question.get("scheduled_resolve_time", "") or
                       question_data.get("scheduled_resolve_time", ""))

        # Get status
        status = question.get("status", "") or question_data.get("status", "")

        # Get resolution (for resolved questions)
        resolution = question.get("resolution") or question_data.get("resolution")

        # Get number of predictions
        num_predictions = (question.get("forecasts_count", 0) or
                          question.get("nr_forecasters", 0) or
                          question.get("number_of_predictions", 0))

        # Get question ID
        q_id = question.get("id")

        return {
            "id": q_id,
            "title": title,
            "description": description,
            "community_prediction": community_prob,  # 0-100 percentage
            "scheduled_close_time": close_time,
            "scheduled_resolve_time": resolve_time,
            "status": status,
            "resolution": resolution,  # 0, 1, or None
            "created_time": question.get("created_at", ""),
            "publish_time": question.get("published_at", ""),
            "url": f"https://www.metaculus.com/questions/{q_id}/",
            "num_predictions": num_predictions,
            "category": self._categorize_question(question),
            # For compatibility with existing code expecting Kalshi format
            "ticker": f"metaculus-{q_id}",
            "yes_bid": community_prob if community_prob else 50,
            "close_time": close_time,
            "volume": num_predictions,
            "subtitle": description[:200] if description else ""
        }

    def _categorize_question(self, question: Dict) -> str:
        """
        Categorize question based on content

        Args:
            question: Question dictionary (raw or processed)

        Returns:
            Category string
        """
        # Handle nested structure
        question_data = question.get('question', {})
        title = (question.get('title', '') or question_data.get('title', '')).lower()
        description = (question.get('description', '') or question_data.get('description', '') or '').lower()
        text = f"{title} {description}"

        for category, keywords in self.LCS_TOPICS.items():
            for keyword in keywords:
                if keyword in text:
                    return category.title()

        return "General"

    def fetch_questions(self, status: str = "open", limit: int = 20,
                       forecast_type: str = "binary") -> List[Dict]:
        """
        Fetch list of prediction questions

        Args:
            status: Question status ('open', 'closed', 'resolved')
            limit: Maximum number of questions to return
            forecast_type: Type of forecast ('binary' recommended)

        Returns:
            List of question dictionaries
        """
        params = {
            "status": status,
            "forecast_type": forecast_type,
            "order_by": "-activity",
            "limit": min(limit, 100)  # Metaculus max is 100
        }

        result = self._make_request("", params)

        if result and "results" in result:
            questions = result["results"]
            processed = []
            for q in questions:
                processed_q = self._process_question(q)
                # Only include questions with community predictions
                if processed_q["community_prediction"] is not None:
                    processed.append(processed_q)
            return processed
        return []

    def fetch_question(self, question_id: int) -> Optional[Dict]:
        """
        Fetch details for a specific question

        Args:
            question_id: Metaculus question ID

        Returns:
            Question details dictionary or None if not found
        """
        result = self._make_request(str(question_id))

        if result:
            return self._process_question(result)
        return None

    def get_community_prediction(self, question_id: int) -> Optional[float]:
        """
        Get the current community prediction for a question

        Args:
            question_id: Metaculus question ID

        Returns:
            Community probability as percentage (0-100) or None
        """
        question = self.fetch_question(question_id)
        if question:
            return question.get("community_prediction")
        return None

    def get_questions_by_topic(self, topic: str, limit: int = 10,
                               include_politics: bool = False) -> List[Dict]:
        """
        Get questions filtered by topic

        Args:
            topic: Topic to filter ('economics', 'finance', 'technology', 'science', 'business')
            limit: Maximum number of questions
            include_politics: Whether to include political questions

        Returns:
            List of questions matching the topic
        """
        # Fetch more questions to filter from
        all_questions = self.fetch_questions(status="open", limit=100)

        filtered = []
        topic_keywords = self.LCS_TOPICS.get(topic.lower(), [topic.lower()])

        for question in all_questions:
            if len(filtered) >= limit:
                break

            title = question.get('title', '').lower()
            description = question.get('description', '').lower()
            text = f"{title} {description}"

            # Check topic match
            topic_match = any(keyword in text for keyword in topic_keywords)

            if topic_match and self._is_lcs_relevant(question, include_politics):
                filtered.append(question)

        return filtered

    def get_lcs_relevant_questions(self, limit: int = 20,
                                   include_politics: bool = False) -> List[Dict]:
        """
        Get questions relevant to LCS topics (economics, finance, tech, science)

        Args:
            limit: Maximum number of questions
            include_politics: Whether to include political questions

        Returns:
            List of LCS-relevant questions
        """
        all_questions = self.fetch_questions(status="open", limit=100)

        filtered = []
        for question in all_questions:
            if len(filtered) >= limit:
                break

            if self._is_lcs_relevant(question, include_politics):
                filtered.append(question)

        return filtered

    def check_resolution(self, question_id: int) -> Dict[str, Any]:
        """
        Check if a question has resolved and get the outcome

        Args:
            question_id: Metaculus question ID

        Returns:
            Dictionary with resolution status and outcome
        """
        question = self.fetch_question(question_id)
        if question:
            status = question.get("status", "")
            resolution = question.get("resolution")

            resolved = status == "resolved" or resolution is not None
            outcome = None
            if resolution is not None:
                # Metaculus resolution: 1 = Yes, 0 = No
                outcome = "yes" if resolution == 1 else "no"

            return {
                "resolved": resolved,
                "outcome": outcome,
                "status": status
            }
        return {
            "resolved": False,
            "outcome": None,
            "status": "unknown"
        }

    def get_diverse_questions(self, topics: List[str],
                              limit_per_topic: int = 3) -> List[Dict]:
        """
        Get a diverse set of questions across multiple topics

        Args:
            topics: List of topic names
            limit_per_topic: Max questions per topic

        Returns:
            List of diverse questions
        """
        all_questions = []
        seen_ids = set()

        for topic in topics:
            topic_questions = self.get_questions_by_topic(topic, limit_per_topic)
            for q in topic_questions:
                if q['id'] not in seen_ids:
                    seen_ids.add(q['id'])
                    all_questions.append(q)

        return all_questions


# Singleton instance for use across the app
_metaculus_client = None

def get_metaculus_client() -> MetaculusClient:
    """Get or create the global Metaculus client instance"""
    global _metaculus_client
    if _metaculus_client is None:
        _metaculus_client = MetaculusClient()
    return _metaculus_client
