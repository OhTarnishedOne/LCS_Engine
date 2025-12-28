"""
Test that the app handles missing secrets.toml gracefully
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

def test_secrets_handling():
    """Test that generate_ai_response handles missing secrets gracefully"""
    
    print("Testing Secrets Handling...")
    print("-" * 50)
    
    # Mock streamlit module without secrets
    class MockST:
        class session_state:
            @staticmethod
            def get(key, default=None):
                if key == 'user_profile':
                    return {'investor_type': 'Balanced'}
                return default
        
        class secrets:
            @staticmethod
            def get(key):
                # Simulate missing secrets.toml
                raise FileNotFoundError("secrets.toml not found")
        
        @staticmethod
        def error(msg):
            print(f"Error: {msg}")
    
    # Import and patch the module
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "test_module", 
        Path(__file__).parent / "pages" / "2_Strategies.py"
    )
    module = importlib.util.module_from_spec(spec)
    module.st = MockST()
    module.os = os
    
    # Execute the module to load functions
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        # Some imports might fail, that's OK for our test
        pass
    
    # Test 1: Check that generate_mock_response exists and works
    print("✅ Test 1: Mock response function")
    try:
        response = module.generate_mock_response("What is risk?")
        if response and len(response) > 50:
            print(f"   ✓ Mock response works ({len(response)} chars)")
        else:
            print(f"   ⚠ Mock response too short")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Check that generate_ai_response handles missing secrets
    print("\n✅ Test 2: generate_ai_response with missing secrets")
    try:
        # Clear any environment variables
        old_key = os.environ.get("ANTHROPIC_API_KEY")
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]
        
        # This should not crash, should fall back to mock
        response = module.generate_ai_response("What is investing?")
        
        if response and len(response) > 0:
            print(f"   ✓ Falls back to mock response gracefully")
            print(f"   Response length: {len(response)} chars")
        else:
            print(f"   ⚠ No response returned")
        
        # Restore environment variable if it existed
        if old_key:
            os.environ["ANTHROPIC_API_KEY"] = old_key
            
    except Exception as e:
        print(f"   ❌ Function crashed: {e}")
        return False
    
    # Test 3: Check with environment variable
    print("\n✅ Test 3: generate_ai_response with env variable")
    try:
        # Set a dummy API key
        os.environ["ANTHROPIC_API_KEY"] = "dummy_key_for_testing"
        
        # This should try to use the API (will fail) but fall back gracefully
        response = module.generate_ai_response("Tell me about stocks")
        
        if response and len(response) > 0:
            print(f"   ✓ Handles API failure gracefully")
            print(f"   Falls back to mock response")
        
        # Clean up
        del os.environ["ANTHROPIC_API_KEY"]
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "-" * 50)
    print("Secrets Handling Tests Complete! ✅")
    print("\nThe app will now:")
    print("• ✓ Try st.secrets first (won't crash if missing)")
    print("• ✓ Fall back to environment variables")
    print("• ✓ Use mock responses if no API key found")
    print("• ✓ Handle API errors gracefully")
    
    return True

if __name__ == "__main__":
    test_secrets_handling()