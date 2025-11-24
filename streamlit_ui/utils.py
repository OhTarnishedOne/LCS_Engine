"""
Utility functions for LCS Streamlit App
"""

import os
import json
import requests
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
from typing import Dict, List, Optional, Tuple
import yfinance as yf

class StockDataClient:
    """Client for fetching real-time stock data"""
    
    def __init__(self, alpha_vantage_key: Optional[str] = None):
        try:
            self.alpha_vantage_key = alpha_vantage_key or st.secrets.get("api_keys", {}).get("ALPHA_VANTAGE_API_KEY") or os.getenv('ALPHA_VANTAGE_API_KEY')
        except:
            self.alpha_vantage_key = None
        self.base_url = "https://www.alphavantage.co/query"
        self.demo_mode = not bool(self.alpha_vantage_key)
    
    def get_quote(self, symbol: str) -> Dict:
        """Get real-time quote for a symbol"""
        try:
            # Try yfinance first (no API key needed)
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'price': info.get('regularMarketPrice', info.get('previousClose', 0)),
                'change': info.get('regularMarketChange', 0),
                'changePercent': info.get('regularMarketChangePercent', 0),
                'volume': info.get('regularMarketVolume', 0),
                'marketCap': info.get('marketCap', 0),
                'name': info.get('longName', symbol)
            }
        except Exception as e:
            # Fallback to Alpha Vantage if available
            if self.alpha_vantage_key:
                return self._get_alpha_vantage_quote(symbol)
            else:
                # Return mock data if no API available
                return self._get_mock_quote(symbol)
    
    def _get_alpha_vantage_quote(self, symbol: str) -> Dict:
        """Get quote from Alpha Vantage API"""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.alpha_vantage_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            
            if 'Global Quote' in data:
                quote = data['Global Quote']
                return {
                    'symbol': symbol,
                    'price': float(quote.get('05. price', 0)),
                    'change': float(quote.get('09. change', 0)),
                    'changePercent': quote.get('10. change percent', '0%'),
                    'volume': int(quote.get('06. volume', 0)),
                    'previousClose': float(quote.get('08. previous close', 0))
                }
        except Exception as e:
            st.warning(f"Error fetching data for {symbol}: {str(e)}")
        
        return self._get_mock_quote(symbol)
    
    def _get_mock_quote(self, symbol: str) -> Dict:
        """Generate mock quote data"""
        import random
        
        mock_prices = {
            "AAPL": 175.50, "GOOGL": 140.25, "MSFT": 380.75,
            "NVDA": 480.50, "TSLA": 250.30, "JNJ": 155.80,
            "SPY": 450.25, "BND": 75.30, "VTI": 220.50
        }
        
        base_price = mock_prices.get(symbol, 100)
        change_pct = random.uniform(-3, 3)
        
        return {
            'symbol': symbol,
            'price': round(base_price * (1 + change_pct/100), 2),
            'change': round(base_price * change_pct/100, 2),
            'changePercent': f"{change_pct:.2f}%",
            'volume': random.randint(1000000, 50000000)
        }
    
    def get_historical_data(self, symbol: str, period: str = "1mo") -> pd.DataFrame:
        """Get historical price data"""
        try:
            ticker = yf.Ticker(symbol)
            return ticker.history(period=period)
        except:
            # Return mock data if API fails
            return self._generate_mock_historical(symbol, period)
    
    def _generate_mock_historical(self, symbol: str, period: str) -> pd.DataFrame:
        """Generate mock historical data"""
        import numpy as np
        
        # Determine number of days based on period
        period_days = {
            "1d": 1, "5d": 5, "1mo": 30,
            "3mo": 90, "6mo": 180, "1y": 365
        }
        days = period_days.get(period, 30)
        
        # Generate dates
        dates = pd.date_range(end=datetime.now(), periods=days)
        
        # Generate mock prices with random walk
        base_price = 100
        returns = np.random.normal(0.001, 0.02, days)
        prices = base_price * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'Close': prices,
            'Open': prices * np.random.uniform(0.98, 1.02, days),
            'High': prices * np.random.uniform(1.01, 1.05, days),
            'Low': prices * np.random.uniform(0.95, 0.99, days),
            'Volume': np.random.randint(1000000, 50000000, days)
        }, index=dates)
        
        return df


class OpenAIClient:
    """Client for OpenAI API integration"""
    
    def __init__(self, api_key: Optional[str] = None):
        try:
            self.api_key = api_key or st.secrets.get("api_keys", {}).get("OPENAI_API_KEY") or os.getenv('OPENAI_API_KEY')
        except:
            self.api_key = None
        self.model = "gpt-3.5-turbo"
        self.demo_mode = not bool(self.api_key)
    
    def generate_strategy_explanation(self, strategy: Dict, user_profile: Dict) -> str:
        """Generate AI explanation for a strategy"""
        
        # For demo, return pre-written explanation
        # In production, would call OpenAI API
        
        risk_explanations = {
            "Conservative": "This strategy prioritizes capital preservation and steady income through dividend-paying stocks and bonds. It's designed to minimize volatility while providing returns that beat inflation.",
            "Aggressive": "This high-growth strategy focuses on companies with strong innovation and expansion potential. While it carries more risk, it offers the possibility of substantial returns over time.",
            "Balanced": "This strategy combines growth potential with stability, mixing established companies with emerging opportunities. It's designed to provide solid returns while managing downside risk."
        }
        
        investor_type = user_profile.get('investor_type', 'Balanced')
        base_explanation = risk_explanations.get(investor_type, risk_explanations['Balanced'])
        
        return f"""
        {base_explanation}
        
        Based on your profile:
        - Timeline: {user_profile.get('investment_timeline', 'Medium-term')}
        - Goal: {user_profile.get('primary_goal', 'Balanced growth')}
        - Experience: {user_profile.get('experience_level', 'Beginner')}
        
        This strategy has been personalized to match your risk tolerance and investment objectives.
        """
    
    def answer_question(self, question: str, context: Dict) -> str:
        """Answer user questions about investing"""
        
        # For demo, use pattern matching
        # In production, would call OpenAI API with context
        
        question_lower = question.lower()
        
        # Common question patterns
        if "risk" in question_lower:
            return self._explain_risk(context)
        elif "dividend" in question_lower:
            return self._explain_dividends()
        elif "etf" in question_lower:
            return self._explain_etfs()
        elif "rebalance" in question_lower:
            return self._explain_rebalancing()
        else:
            return self._generic_response(question)
    
    def _explain_risk(self, context: Dict) -> str:
        return """
        Risk in investing refers to the possibility that your investment may lose value. Different investments carry different levels of risk:
        
        - **Low Risk**: Government bonds, high-grade corporate bonds
        - **Moderate Risk**: Large-cap stocks, balanced funds
        - **High Risk**: Small-cap stocks, emerging markets, cryptocurrencies
        
        Your risk tolerance determines which investments are suitable for you. Based on your profile, we've recommended strategies that match your comfort level with market volatility.
        """
    
    def _explain_dividends(self) -> str:
        return """
        Dividends are payments companies make to shareholders from their profits. Think of them as a "thank you" for owning their stock.
        
        Key points about dividends:
        - Paid quarterly (usually)
        - Provide regular income
        - Can be reinvested to buy more shares
        - Common from established, profitable companies
        
        Dividend stocks are great for investors seeking regular income or those who want to reinvest for compound growth.
        """
    
    def _explain_etfs(self) -> str:
        return """
        ETFs (Exchange-Traded Funds) are like baskets containing many stocks or bonds. Instead of buying individual stocks, you buy shares of the basket.
        
        Benefits of ETFs:
        - **Instant Diversification**: Own hundreds of stocks with one purchase
        - **Lower Risk**: Spread risk across many companies
        - **Lower Fees**: Generally cheaper than mutual funds
        - **Easy to Trade**: Buy and sell like regular stocks
        
        ETFs are perfect for beginners because they provide professional-level diversification with minimal effort.
        """
    
    def _explain_rebalancing(self) -> str:
        return """
        Rebalancing means adjusting your portfolio back to your target allocation. Over time, some investments grow faster than others, throwing off your intended mix.
        
        Example: You start with 60% stocks, 40% bonds. After a year, stocks grow to 70% of your portfolio. Rebalancing means selling some stocks and buying bonds to get back to 60/40.
        
        How often to rebalance:
        - **Quarterly**: Check but only act if significantly off target (>5%)
        - **Annually**: Good for most long-term investors
        - **Threshold-based**: Rebalance when any position is 5-10% off target
        """
    
    def _generic_response(self, question: str) -> str:
        return f"""
        That's a great question about investing! While I don't have a specific answer prepared for "{question}", here are some general principles that might help:
        
        1. **Start Simple**: Begin with broad market ETFs before individual stocks
        2. **Diversify**: Don't put all your eggs in one basket
        3. **Think Long-term**: Time in the market beats timing the market
        4. **Keep Learning**: The more you understand, the better investor you'll become
        
        For specific advice about your situation, consider consulting with a financial advisor.
        """


class AlpacaClient:
    """Client for Alpaca paper trading"""
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        try:
            self.api_key = api_key or st.secrets.get("api_keys", {}).get("ALPACA_API_KEY") or os.getenv('APCA_API_KEY_ID')
            self.secret_key = secret_key or st.secrets.get("api_keys", {}).get("ALPACA_SECRET_KEY") or os.getenv('APCA_API_SECRET_KEY')
        except:
            self.api_key = None
            self.secret_key = None
        self.base_url = "https://paper-api.alpaca.markets"  # Paper trading URL
        self.demo_mode = not bool(self.api_key and self.secret_key)
    
    def create_order(self, symbol: str, qty: int, side: str = 'buy') -> Dict:
        """Create a paper trade order"""
        
        # For demo, return mock order
        # In production, would call Alpaca API
        
        return {
            'id': f"demo_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'symbol': symbol,
            'qty': qty,
            'side': side,
            'type': 'market',
            'status': 'filled',
            'filled_at': datetime.now().isoformat(),
            'filled_price': 100.00  # Would get actual price from API
        }
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        
        # For demo, return mock positions
        # In production, would call Alpaca API
        
        return []
    
    def get_account(self) -> Dict:
        """Get account information"""
        
        # For demo, return mock account
        # In production, would call Alpaca API
        
        return {
            'buying_power': 100000,
            'portfolio_value': 100000,
            'cash': 100000,
            'positions_value': 0
        }


def format_currency(value: float) -> str:
    """Format value as currency"""
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage"""
    return f"{value:.2f}%"


def calculate_portfolio_metrics(positions: List[Dict]) -> Dict:
    """Calculate portfolio performance metrics"""
    
    if not positions:
        return {
            'total_value': 0,
            'total_cost': 0,
            'total_return': 0,
            'total_return_pct': 0
        }
    
    total_value = sum(p.get('market_value', 0) for p in positions)
    total_cost = sum(p.get('cost_basis', 0) for p in positions)
    total_return = total_value - total_cost
    total_return_pct = (total_return / total_cost * 100) if total_cost > 0 else 0
    
    return {
        'total_value': total_value,
        'total_cost': total_cost,
        'total_return': total_return,
        'total_return_pct': total_return_pct
    }


def save_user_session(session_data: Dict) -> str:
    """Save user session to file"""
    
    session_dir = Path(__file__).parent.parent / "lcs_sessions"
    session_dir.mkdir(exist_ok=True)
    
    filename = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = session_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(session_data, f, indent=2, default=str)
    
    return str(filepath)


def load_user_session(filepath: str) -> Dict:
    """Load user session from file"""
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading session: {str(e)}")
        return {}


def get_market_status() -> Dict:
    """Get current market status"""
    
    now = datetime.now()
    market_open = now.replace(hour=9, minute=30, second=0)
    market_close = now.replace(hour=16, minute=0, second=0)
    
    is_weekday = now.weekday() < 5
    is_market_hours = market_open <= now <= market_close
    
    return {
        'is_open': is_weekday and is_market_hours,
        'next_open': market_open if now < market_open else market_open + timedelta(days=1),
        'next_close': market_close if now < market_close else market_close + timedelta(days=1)
    }