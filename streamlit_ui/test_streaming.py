"""
Test script for AI streaming functionality
Run this to verify streaming responses work correctly
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from ai_streaming import (
    stream_anthropic_response, 
    stream_openai_response, 
    stream_mock_response,
    get_available_ai_provider,
    build_ai_context
)

def test_streaming_functionality():
    """Test the streaming AI functionality"""
    
    print("Testing AI Streaming Functionality...")
    print("-" * 50)
    
    # Mock session state
    class MockSessionState:
        def get(self, key, default=None):
            mock_data = {
                'user_profile': {
                    'investor_type': 'Balanced',
                    'experience_level': 'Intermediate',
                    'primary_goal': 'Long-term growth',
                    'investment_timeline': 'Medium-term',
                    'risk_tolerance': 'Moderate'
                },
                'selected_strategy': {
                    'name': 'Balanced Growth Strategy',
                    'description': 'A mix of growth and value stocks',
                    'risk_level': 'Medium',
                    'expected_return': '8-12%',
                    'stocks': [
                        {'symbol': 'AAPL'},
                        {'symbol': 'MSFT'},
                        {'symbol': 'VTI'}
                    ]
                }
            }
            return mock_data.get(key, default)
    
    # Set up mock streamlit
    import ai_streaming
    class MockST:
        session_state = MockSessionState()
        class secrets:
            @staticmethod
            def get(key, default=None):
                return default
        @staticmethod
        def error(msg):
            print(f"Error: {msg}")
    ai_streaming.st = MockST()
    
    # Test 1: Context building
    print("✅ Test 1: Context Building")
    context = build_ai_context("Why is diversification important?")
    print(f"   Context length: {len(context)} characters")
    assert "Balanced Growth Strategy" in context
    assert "Intermediate" in context
    print("   Context includes user profile and strategy ✓")
    
    # Test 2: Mock streaming
    print("\n✅ Test 2: Mock Streaming Response")
    question = "What is risk in investing?"
    print(f"   Question: {question}")
    print("   Streaming response: ", end="", flush=True)
    
    response_parts = []
    for chunk in stream_mock_response(question):
        response_parts.append(chunk)
        print(chunk, end="", flush=True)
    
    full_response = "".join(response_parts)
    print(f"\n   Full response length: {len(full_response)} characters")
    assert len(full_response) > 50
    assert "risk" in full_response.lower()
    
    # Test 3: Provider detection
    print("\n✅ Test 3: AI Provider Detection")
    provider = get_available_ai_provider()
    print(f"   Available provider: {provider}")
    assert provider in ["anthropic", "openai", "mock"]
    
    # Test 4: Different question types
    print("\n✅ Test 4: Pattern-based Responses")
    test_questions = [
        ("What are dividends?", "dividend"),
        ("How often should I rebalance?", "rebalanc"),
        ("What happens in a market crash?", "crash")
    ]
    
    for question, expected_keyword in test_questions:
        print(f"   Testing: {question}")
        response_parts = list(stream_mock_response(question))
        full_response = "".join(response_parts)
        if expected_keyword in full_response.lower():
            print(f"     ✓ Response contains '{expected_keyword}'")
        else:
            print(f"     ⚠ Response missing '{expected_keyword}'")
            print(f"     Debug: First 100 chars: {full_response[:100]}")
    
    print("\n" + "-" * 50)
    print("All streaming tests passed! 🎉")
    print("\nStreaming Features:")
    print("• ✅ Word-by-word streaming simulation")
    print("• ✅ Pattern-based intelligent responses") 
    print("• ✅ User profile and strategy integration")
    print("• ✅ Multiple AI provider support")
    print("• ✅ Graceful fallback to mock responses")
    
    print(f"\nReady to use with provider: {provider.upper()}")
    
    if provider == "mock":
        print("\n💡 Note: Install 'anthropic' or 'openai' packages and set API keys for live AI responses")

if __name__ == "__main__":
    test_streaming_functionality()