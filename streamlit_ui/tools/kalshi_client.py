"""
Kalshi API Client for fetching prediction market data
No authentication required - using public market data endpoints
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import streamlit as st
import time

class KalshiClient:
    """Client for interacting with Kalshi prediction markets API"""
    
    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
    
    def __init__(self):
        self.session = requests.Session()
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 200ms between requests to avoid rate limits
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make a rate-limited request to Kalshi API"""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"API request failed: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            st.error(f"Network error: {str(e)}")
            return None
    
    def fetch_markets(self, status: str = "open", limit: int = 20, 
                     event_ticker: Optional[str] = None) -> List[Dict]:
        """
        Fetch list of prediction markets
        
        Args:
            status: Market status ('open', 'closed', 'settled')
            limit: Maximum number of markets to return
            event_ticker: Filter by event category (optional)
        
        Returns:
            List of market dictionaries
        """
        params = {
            "status": status,
            "limit": limit
        }
        
        if event_ticker:
            params["event_ticker"] = event_ticker
            
        result = self._make_request("markets", params)
        
        if result and "markets" in result:
            markets = result["markets"]
            # Process markets to extract key fields
            processed_markets = []
            for market in markets:
                processed_markets.append({
                    "ticker": market.get("ticker", ""),
                    "title": market.get("title", ""),
                    "subtitle": market.get("subtitle", ""),
                    "yes_bid": market.get("yes_bid", 0),  # Price in cents (0-100)
                    "no_bid": market.get("no_bid", 0),
                    "volume": market.get("volume", 0),
                    "volume_24h": market.get("volume_24h", 0),
                    "close_time": market.get("close_time", ""),
                    "status": market.get("status", ""),
                    "result": market.get("result", None),  # 'yes', 'no', or None
                    "category": market.get("category", ""),
                    "event_ticker": market.get("event_ticker", "")
                })
            return processed_markets
        return []
    
    def fetch_market(self, ticker: str) -> Optional[Dict]:
        """
        Fetch details for a specific market
        
        Args:
            ticker: Market ticker (e.g., "INXD-23DEC31-B4400")
        
        Returns:
            Market details dictionary or None if not found
        """
        result = self._make_request(f"markets/{ticker}")
        
        if result and "market" in result:
            market = result["market"]
            return {
                "ticker": market.get("ticker", ""),
                "title": market.get("title", ""),
                "subtitle": market.get("subtitle", ""),
                "yes_bid": market.get("yes_bid", 0),
                "no_bid": market.get("no_bid", 0),
                "last_price": market.get("last_price", 0),
                "volume": market.get("volume", 0),
                "volume_24h": market.get("volume_24h", 0),
                "close_time": market.get("close_time", ""),
                "status": market.get("status", ""),
                "result": market.get("result", None),
                "category": market.get("category", ""),
                "rules": market.get("rules", ""),
                "event_ticker": market.get("event_ticker", "")
            }
        return None
    
    def fetch_events(self, status: str = "open") -> List[Dict]:
        """
        Fetch list of event categories
        
        Args:
            status: Event status filter
        
        Returns:
            List of event dictionaries with categories
        """
        params = {"status": status, "limit": 100}
        result = self._make_request("events", params)
        
        if result and "events" in result:
            events = result["events"]
            # Extract unique categories
            categories = {}
            for event in events:
                category = event.get("category", "Other")
                ticker = event.get("event_ticker", "")
                title = event.get("title", "")
                
                if category not in categories:
                    categories[category] = []
                
                categories[category].append({
                    "event_ticker": ticker,
                    "title": title,
                    "category": category,
                    "markets_count": event.get("markets_count", 0)
                })
            
            return categories
        return {}
    
    def get_market_price(self, ticker: str) -> Optional[float]:
        """
        Get the current implied probability for a market
        
        Args:
            ticker: Market ticker
        
        Returns:
            Implied probability as percentage (0-100) or None
        """
        market = self.fetch_market(ticker)
        if market:
            return market.get("yes_bid", 0)  # Returns price in cents (0-100)
        return None
    
    def check_resolution(self, ticker: str) -> Dict[str, Any]:
        """
        Check if a market has resolved and get the outcome
        
        Args:
            ticker: Market ticker
        
        Returns:
            Dictionary with resolution status and outcome
        """
        market = self.fetch_market(ticker)
        if market:
            status = market.get("status", "")
            result = market.get("result", None)
            
            return {
                "resolved": status == "settled",
                "outcome": result,  # 'yes' or 'no' if resolved, None otherwise
                "status": status
            }
        return {
            "resolved": False,
            "outcome": None,
            "status": "unknown"
        }
    
    def get_markets_by_category(self, category: str, limit: int = 10) -> List[Dict]:
        """
        Get markets filtered by category
        
        Args:
            category: Category name (e.g., 'Economics', 'Politics', 'Climate')
            limit: Maximum number of markets
        
        Returns:
            List of markets in the specified category
        """
        # First get all open markets
        markets = self.fetch_markets(status="open", limit=100)
        
        # Filter by category (case insensitive)
        filtered = []
        for market in markets:
            market_cat = market.get("category", "").lower()
            if category.lower() in market_cat:
                filtered.append(market)
                if len(filtered) >= limit:
                    break
        
        return filtered
    
    def get_diverse_markets(self, categories: List[str], limit_per_category: int = 3) -> List[Dict]:
        """
        Get a diverse set of markets across multiple categories
        
        Args:
            categories: List of category names
            limit_per_category: Max markets per category
        
        Returns:
            List of diverse markets
        """
        all_markets = []
        for category in categories:
            cat_markets = self.get_markets_by_category(category, limit_per_category)
            all_markets.extend(cat_markets)
        
        return all_markets


# Singleton instance for use across the app
_kalshi_client = None

def get_kalshi_client() -> KalshiClient:
    """Get or create the global Kalshi client instance"""
    global _kalshi_client
    if _kalshi_client is None:
        _kalshi_client = KalshiClient()
    return _kalshi_client