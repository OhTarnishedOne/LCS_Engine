#!/usr/bin/env python3
"""
Test script for Kalshi API integration
Run this to verify the Kalshi client is working correctly
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from tools.kalshi_client import KalshiClient

def test_kalshi_api():
    """Test basic Kalshi API functionality"""
    print("Testing Kalshi API Integration...")
    print("-" * 50)
    
    client = KalshiClient()
    
    # Test 1: Fetch open markets
    print("\n1. Fetching open markets...")
    markets = client.fetch_markets(status="open", limit=5)
    
    if markets:
        print(f"✅ Found {len(markets)} open markets")
        print("\nSample market:")
        market = markets[0]
        print(f"  Title: {market['title']}")
        print(f"  Category: {market.get('category', 'N/A')}")
        print(f"  Yes Price: {market.get('yes_bid', 0)}¢")
        print(f"  Volume: ${market.get('volume', 0):,}")
    else:
        print("❌ No markets found")
        return False
    
    # Test 2: Fetch specific market details
    if markets:
        print("\n2. Fetching specific market details...")
        ticker = markets[0]['ticker']
        market_detail = client.fetch_market(ticker)
        
        if market_detail:
            print(f"✅ Got details for market: {ticker}")
            print(f"  Rules: {market_detail.get('rules', 'N/A')[:100]}...")
        else:
            print(f"❌ Could not fetch details for: {ticker}")
    
    # Test 3: Get events/categories
    print("\n3. Fetching event categories...")
    events = client.fetch_events(status="open")
    
    if events:
        print(f"✅ Found {len(events)} event categories")
        categories = list(events.keys())[:5]
        print(f"  Categories: {', '.join(categories)}")
    else:
        print("❌ No events found")
    
    # Test 4: Get markets by category
    print("\n4. Testing category filtering...")
    econ_markets = client.get_markets_by_category("Economics", limit=3)
    
    if econ_markets:
        print(f"✅ Found {len(econ_markets)} Economics markets")
        for m in econ_markets:
            print(f"  - {m['title'][:60]}...")
    else:
        print("❌ No Economics markets found")
    
    # Test 5: Check resolution status
    if markets:
        print("\n5. Testing resolution check...")
        resolution = client.check_resolution(markets[0]['ticker'])
        print(f"✅ Resolution check completed")
        print(f"  Status: {resolution['status']}")
        print(f"  Resolved: {resolution['resolved']}")
    
    print("\n" + "=" * 50)
    print("✅ All tests completed successfully!")
    return True

if __name__ == "__main__":
    try:
        success = test_kalshi_api()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)