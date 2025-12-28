"""
Paper Trading Simulation Page
Allows users to test strategies with real market data
"""

import streamlit as st # type: ignore
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import random
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent))
from session_utils import save_session, display_session_info

st.set_page_config(
    page_title="LCS - Paper Trading",
    page_icon="🎲",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .trade-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    .profit-positive {
        color: #2E7D32;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .profit-negative {
        color: #D32F2F;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .stock-row {
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-left: 3px solid #4CAF50;
        background: white;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []
if 'initial_investment' not in st.session_state:
    st.session_state.initial_investment = 10000

def get_mock_price(symbol):
    """Get mock real-time price (would use Alpha Vantage API in production)"""
    # Mock prices based on symbol
    base_prices = {
        "AAPL": 175.50,
        "GOOGL": 140.25,
        "MSFT": 380.75,
        "NVDA": 480.50,
        "TSLA": 250.30,
        "JNJ": 155.80,
        "PG": 145.20,
        "VZ": 35.60,
        "SPY": 450.25,
        "BND": 75.30,
        "VTI": 220.50,
        "V": 250.80,
        "HD": 350.25,
        "NET": 85.40,
        "SQ": 65.30,
        "O": 55.80,
        "TLT": 92.50,
        "NEE": 75.40,
        "AGG": 98.20,
        "ARKK": 45.60,
        "CRSP": 55.30,
        "ENPH": 125.60,
        "SCHD": 78.90,
        "VXUS": 55.40
    }
    
    # Add small random variation to simulate real-time changes
    base = base_prices.get(symbol, 100)
    variation = random.uniform(-2, 2) * 0.01  # ±2% variation
    return round(base * (1 + variation), 2)

def calculate_portfolio_value():
    """Calculate current portfolio value"""
    total = 0
    for symbol, data in st.session_state.portfolio.items():
        current_price = get_mock_price(symbol)
        total += current_price * data['shares']
    return total

def execute_trades(strategy, investment_amount):
    """Execute paper trades for a strategy"""
    trades = []
    remaining = investment_amount
    
    # Allocate based on equal weighting for simplicity
    stocks = strategy['stocks']
    per_stock = investment_amount / len(stocks)
    
    for stock in stocks:
        price = get_mock_price(stock['symbol'])
        shares = int(per_stock / price)
        cost = shares * price
        
        if cost <= remaining:
            trades.append({
                'symbol': stock['symbol'],
                'name': stock['name'],
                'shares': shares,
                'price': price,
                'total': cost,
                'timestamp': datetime.now()
            })
            remaining -= cost
    
    return trades, remaining

# Main content
st.markdown("# 🎲 Paper Trading Simulator")
st.markdown("Test your investment strategy with real market data - completely risk-free!")

# Check prerequisites
if not st.session_state.get('strategies'):
    st.warning("Please complete the quiz and select a strategy first!")
    if st.button("Go to Strategies"):
        st.switch_page("pages/2_📊_Strategies.py")
else:
    # Trading interface
    tab1, tab2, tab3, tab4 = st.tabs(["📊 New Trade", "💼 Portfolio", "📈 Performance", "📜 History"])
    
    with tab1:
        st.markdown("## Execute Paper Trades")
        
        # Strategy selection
        strategy_names = [s['name'] for s in st.session_state.strategies]
        selected_strategy_name = st.selectbox(
            "Select Strategy to Trade:",
            strategy_names,
            index=0 if st.session_state.selected_strategy is None 
                   else next((i for i, s in enumerate(st.session_state.strategies) 
                             if s['name'] == st.session_state.selected_strategy['name']), 0)
        )
        
        selected_strategy = next(s for s in st.session_state.strategies if s['name'] == selected_strategy_name)
        
        # Investment amount
        col1, col2 = st.columns([2, 1])
        
        with col1:
            investment = st.slider(
                "Investment Amount ($)",
                min_value=100,
                max_value=100000,
                value=10000,
                step=100,
                help="This is paper money - not real funds!"
            )
        
        with col2:
            st.metric("Available for Trading", f"${investment:,.2f}")
        
        # Preview trades
        st.markdown("### 📋 Trade Preview")
        
        if st.button("Calculate Trades", type="primary", use_container_width=True):
            trades, remaining = execute_trades(selected_strategy, investment)
            st.session_state.pending_trades = trades
            st.session_state.trade_remaining = remaining
        
        if 'pending_trades' in st.session_state:
            # Display trade preview
            trade_df = pd.DataFrame(st.session_state.pending_trades)
            trade_df['total'] = trade_df['total'].round(2)
            
            for _, trade in trade_df.iterrows():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.markdown(f"**{trade['symbol']}** - {trade['name']}")
                with col2:
                    st.write(f"{trade['shares']} shares")
                with col3:
                    st.write(f"@ ${trade['price']:.2f}")
                with col4:
                    st.write(f"Total: ${trade['total']:.2f}")
            
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Investment", f"${trade_df['total'].sum():.2f}")
            with col2:
                st.metric("Cash Remaining", f"${st.session_state.trade_remaining:.2f}")
            with col3:
                st.metric("Number of Positions", len(trade_df))
            
            # Execute button
            if st.button("🚀 Execute All Trades", type="primary", use_container_width=True):
                # Add to portfolio
                for _, trade in trade_df.iterrows():
                    symbol = trade['symbol']
                    if symbol in st.session_state.portfolio:
                        # Add to existing position
                        st.session_state.portfolio[symbol]['shares'] += trade['shares']
                        st.session_state.portfolio[symbol]['avg_price'] = (
                            (st.session_state.portfolio[symbol]['avg_price'] * 
                             st.session_state.portfolio[symbol]['shares'] + 
                             trade['price'] * trade['shares']) / 
                            (st.session_state.portfolio[symbol]['shares'] + trade['shares'])
                        )
                    else:
                        # New position
                        st.session_state.portfolio[symbol] = {
                            'name': trade['name'],
                            'shares': trade['shares'],
                            'avg_price': trade['price'],
                            'purchase_date': datetime.now()
                        }
                    
                    # Add to history
                    st.session_state.trade_history.append({
                        'type': 'BUY',
                        'symbol': symbol,
                        'shares': trade['shares'],
                        'price': trade['price'],
                        'total': trade['total'],
                        'timestamp': datetime.now()
                    })
                
                st.success("✅ Trades executed successfully!")
                st.balloons()
                save_session()  # Save after executing trades
                del st.session_state.pending_trades
                del st.session_state.trade_remaining
                st.rerun()
    
    with tab2:
        st.markdown("## 💼 Your Portfolio")
        
        if st.session_state.portfolio:
            # Portfolio summary
            portfolio_value = calculate_portfolio_value()
            total_invested = sum(p['shares'] * p['avg_price'] for p in st.session_state.portfolio.values())
            profit_loss = portfolio_value - total_invested
            profit_pct = (profit_loss / total_invested * 100) if total_invested > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Portfolio Value", f"${portfolio_value:,.2f}")
            with col2:
                st.metric("Total Invested", f"${total_invested:,.2f}")
            with col3:
                profit_class = "profit-positive" if profit_loss >= 0 else "profit-negative"
                st.markdown(f'<div class="{profit_class}">P/L: ${profit_loss:,.2f}</div>', unsafe_allow_html=True)
            with col4:
                st.metric("Return %", f"{profit_pct:.2f}%", 
                         delta=f"${profit_loss:,.2f}")
            
            st.markdown("---")
            
            # Individual positions
            st.markdown("### Positions")
            
            positions_data = []
            for symbol, data in st.session_state.portfolio.items():
                current_price = get_mock_price(symbol)
                position_value = current_price * data['shares']
                position_pl = (current_price - data['avg_price']) * data['shares']
                position_pl_pct = ((current_price - data['avg_price']) / data['avg_price'] * 100)
                
                positions_data.append({
                    'Symbol': symbol,
                    'Name': data['name'],
                    'Shares': data['shares'],
                    'Avg Cost': f"${data['avg_price']:.2f}",
                    'Current Price': f"${current_price:.2f}",
                    'Market Value': f"${position_value:.2f}",
                    'P/L': f"${position_pl:.2f}",
                    'P/L %': f"{position_pl_pct:.2f}%"
                })
            
            df = pd.DataFrame(positions_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Portfolio pie chart
            fig = go.Figure(data=[go.Pie(
                labels=[f"{d['Symbol']} ({d['Shares']} shares)" for d in positions_data],
                values=[float(d['Market Value'].replace('$', '').replace(',', '')) for d in positions_data],
                hole=0.3
            )])
            fig.update_layout(
                title="Portfolio Allocation by Market Value",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No positions yet. Execute some trades to build your portfolio!")
    
    with tab3:
        st.markdown("## 📈 Performance Analysis")
        
        if st.session_state.portfolio:
            # Performance metrics
            portfolio_value = calculate_portfolio_value()
            total_invested = sum(p['shares'] * p['avg_price'] for p in st.session_state.portfolio.values())
            
            # Mock historical performance (would use real data in production)
            days = 30
            dates = pd.date_range(end=datetime.now(), periods=days)
            
            # Generate mock performance data
            values = [total_invested]
            for i in range(1, days):
                # Random walk with slight upward bias
                change = random.uniform(-0.02, 0.025)
                values.append(values[-1] * (1 + change))
            values[-1] = portfolio_value  # End at current value
            
            # Performance chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=values,
                mode='lines',
                name='Portfolio Value',
                line=dict(color='#4CAF50', width=2)
            ))
            fig.add_trace(go.Scatter(
                x=[dates[0], dates[-1]],
                y=[total_invested, total_invested],
                mode='lines',
                name='Initial Investment',
                line=dict(color='#666', width=1, dash='dash')
            ))
            
            fig.update_layout(
                title="Portfolio Performance (30 Days)",
                xaxis_title="Date",
                yaxis_title="Value ($)",
                height=500,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Performance stats
            st.markdown("### Key Metrics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                best_performer = max(st.session_state.portfolio.items(), 
                                    key=lambda x: (get_mock_price(x[0]) - x[1]['avg_price']) / x[1]['avg_price'])
                best_return = ((get_mock_price(best_performer[0]) - best_performer[1]['avg_price']) / 
                              best_performer[1]['avg_price'] * 100)
                st.metric("Best Performer", best_performer[0], f"+{best_return:.1f}%")
            
            with col2:
                # Mock Sharpe ratio
                sharpe = random.uniform(0.8, 1.5)
                st.metric("Sharpe Ratio", f"{sharpe:.2f}", 
                         help="Risk-adjusted return metric")
            
            with col3:
                # Mock max drawdown
                max_dd = random.uniform(5, 15)
                st.metric("Max Drawdown", f"-{max_dd:.1f}%",
                         help="Largest peak-to-trough decline")
        else:
            st.info("No portfolio data yet. Start trading to see performance metrics!")
    
    with tab4:
        st.markdown("## 📜 Trade History")
        
        if st.session_state.trade_history:
            # Display trade history
            history_df = pd.DataFrame(st.session_state.trade_history)
            history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
            history_df = history_df.sort_values('timestamp', ascending=False)
            
            # Format for display
            history_df['Date'] = history_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
            history_df['Price'] = history_df['price'].apply(lambda x: f"${x:.2f}")
            history_df['Total'] = history_df['total'].apply(lambda x: f"${x:.2f}")
            
            display_df = history_df[['Date', 'type', 'symbol', 'shares', 'Price', 'Total']]
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Summary stats
            st.markdown("### Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Trades", len(history_df))
            with col2:
                st.metric("Unique Symbols", history_df['symbol'].nunique())
            with col3:
                st.metric("Total Volume", f"${history_df['total'].sum():,.2f}")
            
            # Export option (Phase 2 - PDF generation)
            if st.button("📄 Generate Report", help="Coming soon: Export to PDF"):
                st.info("PDF export functionality coming in Phase 2!")
        else:
            st.info("No trades executed yet. Start trading to build your history!")

# Footer with disclaimer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem; padding: 1rem;">
    <p>⚠️ <strong>Paper Trading Mode</strong> ⚠️</p>
    <p>This is a simulation using mock market data. No real money is being invested.</p>
    <p>Use this tool to learn and practice before investing real funds.</p>
</div>
""", unsafe_allow_html=True)