"""
Streaming AI responses for LCS Engine
Supports both Anthropic Claude and OpenAI with streaming
"""

try:
    import streamlit as st
except ImportError:
    # For testing purposes when streamlit is not available
    class MockST:
        class session_state:
            @staticmethod
            def get(key, default=None):
                return default
        
        secrets = type('secrets', (), {'get': lambda key, default=None: default})()
        
        @staticmethod
        def error(msg):
            print(f"Error: {msg}")
        @staticmethod  
        def empty():
            class Empty:
                def markdown(self, text, unsafe_allow_html=False):
                    pass
            return Empty()
        @staticmethod
        def spinner(text):
            class Spinner:
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
            return Spinner()
    st = MockST()

import os
import time
from typing import Generator, Dict, Optional

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

def build_ai_context(question: str) -> str:
    """Build context for AI response from user profile and selected strategy"""
    
    profile = st.session_state.get('user_profile', {})
    selected_strategy = st.session_state.get('selected_strategy')
    
    context = f"""You are an investment education assistant helping a user understand their personalized investment strategy.

User Profile:
- Investor Type: {profile.get('investor_type', 'Not specified')}
- Experience Level: {profile.get('experience_level', 'Not specified')}
- Investment Goals: {profile.get('primary_goal', 'Not specified')}
- Time Horizon: {profile.get('investment_timeline', 'Not specified')}
- Risk Tolerance: {profile.get('risk_tolerance', 'Not specified')}
"""
    
    if selected_strategy:
        context += f"""
Currently Discussing Strategy: {selected_strategy['name']}
- Description: {selected_strategy['description']}
- Risk Level: {selected_strategy['risk_level']}
- Expected Return: {selected_strategy['expected_return']}
- Recommended Stocks: {', '.join([s['symbol'] for s in selected_strategy['stocks']])}
"""
    
    context += """
Guidelines:
- Provide educational, easy-to-understand explanations
- Reference the user's profile and selected strategy when relevant
- Avoid giving specific buy/sell advice
- Encourage learning and understanding over quick answers
- Be conversational and supportive
- Keep responses concise but informative
"""
    
    return f"{context}\n\nUser Question: {question}"

def stream_anthropic_response(question: str) -> Generator[str, None, None]:
    """Stream response from Anthropic Claude API"""
    
    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY"))
    
    if not api_key or not ANTHROPIC_AVAILABLE:
        # Fallback to mock streaming
        yield from stream_mock_response(question)
        return
    
    try:
        client = Anthropic(api_key=api_key)
        context = build_ai_context(question)
        
        # Create streaming request
        stream = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Updated to latest model
            max_tokens=1024,
            messages=[
                {"role": "user", "content": context}
            ],
            stream=True
        )
        
        # Stream the response
        for chunk in stream:
            if chunk.type == "content_block_delta":
                if hasattr(chunk.delta, 'text'):
                    yield chunk.delta.text
        
    except Exception as e:
        st.error(f"Anthropic API Error: {str(e)}")
        yield from stream_mock_response(question)

def stream_openai_response(question: str) -> Generator[str, None, None]:
    """Stream response from OpenAI API"""
    
    api_key = st.secrets.get("api_keys", {}).get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    if not api_key or not OPENAI_AVAILABLE:
        # Fallback to mock streaming
        yield from stream_mock_response(question)
        return
    
    try:
        client = openai.OpenAI(api_key=api_key)
        context = build_ai_context(question)
        
        # Create streaming request
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": context}
            ],
            max_tokens=1024,
            stream=True
        )
        
        # Stream the response
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        st.error(f"OpenAI API Error: {str(e)}")
        yield from stream_mock_response(question)

def stream_mock_response(question: str) -> Generator[str, None, None]:
    """Generate mock streaming response when APIs are unavailable"""
    
    question_lower = question.lower()
    
    # Pattern-based responses
    if any(word in question_lower for word in ['risk', 'volatile', 'safe']):
        response = """Risk in investing refers to the possibility that your investment might lose value. Different investments have different risk levels:

• **Conservative investments** (bonds, dividend stocks) have lower risk but also lower potential returns
• **Aggressive investments** (growth stocks, emerging markets) have higher risk but higher potential returns

Your risk tolerance should match your timeline and financial goals. Since you're a {investor_type} investor, this strategy balances risk and reward appropriately for your profile."""
        
    elif any(word in question_lower for word in ['dividend', 'income', 'yield']):
        response = """Dividends are cash payments that companies make to shareholders, usually quarterly. They're like getting paid for owning stock!

• **Dividend stocks** provide regular income and tend to be more stable
• **Growth stocks** typically don't pay dividends - they reinvest profits for expansion
• **Dividend yield** shows how much you earn per year as a percentage of stock price

For your investment timeline, dividends can provide steady income while you wait for long-term growth."""
        
    elif any(word in question_lower for word in ['rebalance', 'maintain', 'adjust', 'often']):
        response = """Rebalancing means adjusting your portfolio back to your target allocation. Here's why it's important:

• Over time, some investments grow faster than others
• This can make your portfolio riskier (or more conservative) than intended
• Rebalancing involves selling high-performing assets and buying underperforming ones

For most investors, rebalancing every 6-12 months is sufficient. Given your {investor_type} strategy, consider rebalancing when any asset class is more than 5-10% away from your target."""
        
    elif any(word in question_lower for word in ['crash', 'bear market', 'downturn']):
        response = """Market crashes are scary but normal parts of investing. Here's what to know:

• The stock market has recovered from every crash in history
• Crashes can actually be buying opportunities for long-term investors
• Having a diversified portfolio helps reduce impact
• Your {investor_type} strategy is designed to weather market volatility

The key is staying calm and sticking to your long-term plan. Don't panic sell - that's when people lose money permanently."""
        
    else:
        response = f"""That's a great question! Based on your profile as a {st.session_state.get('user_profile', {}).get('investor_type', 'balanced')} investor, I'd recommend focusing on the fundamentals.

Remember that investing is a long-term journey, and education is your best tool for success. Your personalized strategy is designed to match your goals and risk tolerance.

Would you like me to explain any specific aspect of your investment strategy in more detail?"""
    
    # Format response with user's investor type
    investor_type = st.session_state.get('user_profile', {}).get('investor_type', 'balanced')
    response = response.format(investor_type=investor_type.lower())
    
    # Stream word by word with slight delays to simulate real streaming
    words = response.split()
    for i, word in enumerate(words):
        if i == 0:
            yield word
        else:
            yield " " + word
        time.sleep(0.03)  # Small delay for realistic streaming effect

def stream_ai_response(question: str, provider: str = "anthropic") -> Generator[str, None, None]:
    """Main function to stream AI response using specified provider"""
    
    if provider == "anthropic":
        yield from stream_anthropic_response(question)
    elif provider == "openai":
        yield from stream_openai_response(question)
    else:
        yield from stream_mock_response(question)

def get_available_ai_provider() -> str:
    """Determine which AI provider to use based on availability"""
    
    # Check Anthropic
    anthropic_key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY"))
    if anthropic_key and ANTHROPIC_AVAILABLE:
        return "anthropic"
    
    # Check OpenAI
    openai_key = st.secrets.get("api_keys", {}).get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if openai_key and OPENAI_AVAILABLE:
        return "openai"
    
    # Fallback to mock
    return "mock"

def display_streaming_response(question: str, provider: Optional[str] = None):
    """Display a streaming AI response in the Streamlit interface"""
    
    if provider is None:
        provider = get_available_ai_provider()
    
    # Create a placeholder for the streaming response
    response_placeholder = st.empty()
    full_response = ""
    
    # Stream the response
    for chunk in stream_ai_response(question, provider):
        full_response += chunk
        response_placeholder.markdown(f'<div class="chat-message assistant-message">🤖 {full_response}▌</div>', unsafe_allow_html=True)
        time.sleep(0.01)  # Small delay for better visual effect
    
    # Final display without cursor
    response_placeholder.markdown(f'<div class="chat-message assistant-message">🤖 {full_response}</div>', unsafe_allow_html=True)
    
    return full_response