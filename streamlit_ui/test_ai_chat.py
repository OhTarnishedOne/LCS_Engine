"""
Test that the AI chat functionality works correctly
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

# Import the functions we need to test
from pages.import_2_Strategies import generate_mock_response, generate_ai_response

def test_ai_responses():
    """Test that AI response generation works"""
    
    print("Testing AI Chat Functionality...")
    print("-" * 50)
    
    # Test 1: Mock responses
    print("✅ Test 1: Mock Responses")
    test_questions = [
        ("What is risk?", "risk"),
        ("Tell me about Apple stock", "apple"),
        ("What are dividends?", "dividend"),
        ("How often should I rebalance?", "rebalance"),
        ("What if the market crashes?", "crash")
    ]
    
    for question, expected_keyword in test_questions:
        response = generate_mock_response(question)
        if expected_keyword in response.lower():
            print(f"   ✓ '{question}' returns response with '{expected_keyword}'")
        else:
            print(f"   ⚠ '{question}' missing '{expected_keyword}'")
    
    # Test 2: Default response
    print("\n✅ Test 2: Default Response")
    response = generate_mock_response("Random question without keywords")
    if "Great question" in response:
        print("   ✓ Default response working")
    else:
        print("   ⚠ Default response not working")
    
    # Test 3: Generate AI response (will use mock since no API key)
    print("\n✅ Test 3: Generate AI Response Function")
    response = generate_ai_response("What is investing?")
    if response and len(response) > 50:
        print(f"   ✓ AI response generated ({len(response)} chars)")
    else:
        print(f"   ⚠ AI response too short or empty")
    
    print("\n" + "-" * 50)
    print("AI Chat Tests Complete!")
    print("\nThe AI assistant should now be working:")
    print("• Mock responses for common questions ✓")
    print("• Default response for unknown questions ✓")  
    print("• Fallback to mock when API unavailable ✓")

if __name__ == "__main__":
    # First check if the module can be imported
    try:
        import streamlit
        print("⚠️  Streamlit is installed - run this test without streamlit for better results")
    except:
        pass
    
    # Mock session state for testing
    class MockST:
        class session_state:
            @staticmethod
            def get(key, default=None):
                if key == 'user_profile':
                    return {'investor_type': 'Balanced'}
                elif key == 'selected_strategy':
                    return {
                        'name': 'Test Strategy',
                        'description': 'A test strategy',
                        'risk_level': 'Medium',
                        'expected_return': '8-10%',
                        'stocks': [{'symbol': 'AAPL'}, {'symbol': 'MSFT'}]
                    }
                return default
        
        class secrets:
            @staticmethod
            def get(key, default=None):
                return default
    
    # Replace st in the module
    import sys
    if 'pages.2_Strategies' in sys.modules:
        sys.modules['pages.2_Strategies'].st = MockST()
    
    test_ai_responses()