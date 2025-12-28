"""
Test script to verify datetime serialization fix in session_manager
"""

import json
from datetime import datetime
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from session_manager import DateTimeEncoder, datetime_decoder

def test_datetime_serialization():
    """Test that datetime objects can be serialized and deserialized"""
    
    print("Testing DateTime Serialization Fix...")
    print("-" * 50)
    
    # Create test data with datetime objects
    test_portfolio = {
        "AAPL": {
            "shares": 10,
            "avg_price": 150.00,
            "purchase_date": datetime.now()
        },
        "MSFT": {
            "shares": 5,
            "avg_price": 300.00,
            "purchase_date": datetime.now()
        }
    }
    
    test_trade_history = [
        {
            "symbol": "AAPL",
            "action": "buy",
            "shares": 10,
            "price": 150.00,
            "total": 1500.00,
            "timestamp": datetime.now()
        },
        {
            "symbol": "MSFT",
            "action": "buy",
            "shares": 5,
            "price": 300.00,
            "total": 1500.00,
            "timestamp": datetime.now()
        }
    ]
    
    # Test 1: Serialize portfolio with datetime objects
    print("✅ Test 1: Serializing portfolio with datetime objects")
    try:
        portfolio_json = json.dumps(test_portfolio, cls=DateTimeEncoder)
        print(f"   Portfolio serialized successfully")
        print(f"   JSON length: {len(portfolio_json)} characters")
        assert "T" in portfolio_json  # ISO format includes 'T'
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 2: Serialize trade history with datetime objects
    print("\n✅ Test 2: Serializing trade history with datetime objects")
    try:
        trades_json = json.dumps(test_trade_history, cls=DateTimeEncoder)
        print(f"   Trade history serialized successfully")
        print(f"   JSON length: {len(trades_json)} characters")
        assert "timestamp" in trades_json
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 3: Deserialize portfolio back to objects
    print("\n✅ Test 3: Deserializing portfolio with datetime strings")
    try:
        loaded_portfolio = json.loads(portfolio_json, object_hook=datetime_decoder)
        print(f"   Portfolio deserialized successfully")
        
        # Check if datetime objects were restored
        for symbol, data in loaded_portfolio.items():
            if isinstance(data.get('purchase_date'), datetime):
                print(f"   ✓ {symbol} purchase_date is a datetime object")
            else:
                print(f"   ⚠ {symbol} purchase_date is not a datetime: {type(data.get('purchase_date'))}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 4: Deserialize trade history back to objects
    print("\n✅ Test 4: Deserializing trade history with datetime strings")
    try:
        loaded_trades = json.loads(trades_json, object_hook=datetime_decoder)
        print(f"   Trade history deserialized successfully")
        print(f"   Number of trades: {len(loaded_trades)}")
        
        # Check if datetime objects were restored
        for i, trade in enumerate(loaded_trades):
            if isinstance(trade.get('timestamp'), datetime):
                print(f"   ✓ Trade {i+1} timestamp is a datetime object")
            else:
                print(f"   ⚠ Trade {i+1} timestamp is not a datetime: {type(trade.get('timestamp'))}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 5: Test with nested structures
    print("\n✅ Test 5: Testing nested structures with datetime objects")
    complex_data = {
        "user_profile": {
            "created_at": datetime.now(),
            "investor_type": "Balanced"
        },
        "strategies": [
            {"name": "Strategy 1", "created": datetime.now()},
            {"name": "Strategy 2", "created": datetime.now()}
        ],
        "portfolio": test_portfolio,
        "trade_history": test_trade_history
    }
    
    try:
        complex_json = json.dumps(complex_data, cls=DateTimeEncoder)
        loaded_complex = json.loads(complex_json, object_hook=datetime_decoder)
        
        # Verify datetime objects in nested structure
        assert isinstance(loaded_complex['user_profile']['created_at'], datetime)
        assert isinstance(loaded_complex['strategies'][0]['created'], datetime)
        assert isinstance(loaded_complex['portfolio']['AAPL']['purchase_date'], datetime)
        assert isinstance(loaded_complex['trade_history'][0]['timestamp'], datetime)
        
        print(f"   Complex nested structure handled correctly")
        print(f"   All datetime objects preserved through serialization")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    print("\n" + "-" * 50)
    print("All datetime serialization tests passed! ✅")
    print("\nThe session manager can now safely:")
    print("• Save portfolios with datetime timestamps")
    print("• Save trade history with datetime objects")
    print("• Restore datetime objects when loading sessions")
    print("• Handle complex nested structures with datetime fields")
    
    return True

if __name__ == "__main__":
    test_datetime_serialization()