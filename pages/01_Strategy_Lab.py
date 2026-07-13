import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from components.ui import load_custom_css, render_header, render_status_sidebar, format_currency, render_currency_selector, render_top_left_logo
from database.db_manager import get_watchlist, log_backtest
from utils.data_loader import fetch_ticker_data
from strategies.list import run_ma_crossover_strategy, run_rsi_reversion_strategy, run_bb_breakout_strategy
from backtesting.engine import run_backtest
from charts.terminal import plot_equity_curve, plot_candlestick_chart

# Page Config
st.set_page_config(page_title="Strategy Lab | QuantLab", page_icon="🧪", layout="wide")
load_custom_css()

# Branding & Currency configs
render_top_left_logo()
render_status_sidebar()
render_currency_selector()

render_header("Strategy Backtesting Lab", "Develop, optimize, and backtest systematic trading strategies")

# Get watchlist tickers
watchlist_items = get_watchlist()
ticker_options = [item['ticker'] for item in watchlist_items] if watchlist_items else ["AAPL", "MSFT", "TSLA"]

# Main Page Configurations Layout
st.markdown("### Strategy Simulator Settings")
config_col1, config_col2, config_col3 = st.columns([1, 1, 1])

with config_col1:
    selected_ticker = st.selectbox("Select Asset Ticker", options=ticker_options)
    strategy_type = st.selectbox(
        "Select Backtest Strategy",
        options=["Moving Average Crossover", "RSI Mean Reversion", "Bollinger Bands Breakout"]
    )
    
with config_col2:
    start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=365))
    end_date = st.date_input("End Date", value=datetime.now())
    
with config_col3:
    curr_symbol = format_currency(1.0, symbol_only=True)
    initial_cap = st.number_input(f"Initial Capital ({curr_symbol})", min_value=1000.0, value=100000.0, step=5000.0)
    commission_pct = st.slider("Slippage & Commission (%)", min_value=0.0, max_value=1.0, value=0.1, step=0.05) / 100.0
    chart_style = st.selectbox("Price Chart Style", options=["Candlestick", "Line Graph"])

# Render strategy specific params on main page
st.markdown("#### Strategy Parameters")
param_col1, param_col2 = st.columns([1, 1])
strategy_params = {}

if strategy_type == "Moving Average Crossover":
    with param_col1:
        strategy_params['fast'] = st.number_input("Fast SMA Period", min_value=2, max_value=100, value=10)
    with param_col2:
        strategy_params['slow'] = st.number_input("Slow SMA Period", min_value=5, max_value=250, value=30)
    
elif strategy_type == "RSI Mean Reversion":
    with param_col1:
        strategy_params['period'] = st.number_input("RSI Period", min_value=2, max_value=50, value=14)
        strategy_params['oversold'] = st.slider("Oversold Level (Buy)", min_value=5, max_value=50, value=30)
    with param_col2:
        strategy_params['overbought'] = st.slider("Overbought Level (Sell)", min_value=50, max_value=95, value=70)
    
elif strategy_type == "Bollinger Bands Breakout":
    with param_col1:
        strategy_params['period'] = st.number_input("BB Period", min_value=5, max_value=100, value=20)
    with param_col2:
        strategy_params['std_multiplier'] = st.slider("Std Dev Multiplier", min_value=1.0, max_value=4.0, value=2.0, step=0.1)

st.markdown("<br/>", unsafe_allow_html=True)
run_clicked = st.button("Run Backtest Execution 🧪", use_container_width=True, type="primary")

# Main Page Results logic
if run_clicked:
    with st.spinner("Fetching market data and simulating execution paths..."):
        # Adjust initial capital if user input is in INR (we normalize internal simulation back to USD and convert back for displays)
        sim_cap = initial_cap
        if st.session_state.get('currency', 'USD') == 'INR':
            sim_cap = initial_cap / 83.0
            
        df = fetch_ticker_data(selected_ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        
        if df.empty or len(df) < 50:
            st.error("Insufficient market data for selected timeline. Try expanding dates.")
        else:
            # Run strategy logic
            if strategy_type == "Moving Average Crossover":
                df_with_signals = run_ma_crossover_strategy(df, strategy_params['fast'], strategy_params['slow'])
            elif strategy_type == "RSI Mean Reversion":
                df_with_signals = run_rsi_reversion_strategy(
                    df, strategy_params['period'], strategy_params['oversold'], strategy_params['overbought']
                )
            elif strategy_type == "Bollinger Bands Breakout":
                df_with_signals = run_bb_breakout_strategy(
                    df, strategy_params['period'], strategy_params['std_multiplier']
                )
            
            # Run backtester
            results = run_backtest(df_with_signals, initial_capital=sim_cap, fee_pct=commission_pct)
            
            # Log results to db
            log_backtest(selected_ticker, strategy_type, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), results['metrics'])
            
            # Draw UI
            st.success("Strategy simulation completed!")
            
            metrics = results['metrics']
            
            # Metrics Cards Row
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                ret_pct = metrics['total_return']
                color = "green" if ret_pct >= 0 else "red"
                st.markdown(f"""
                    <div class="terminal-card">
                        <div class="terminal-card-header">Total Return</div>
                        <div class="terminal-card-value" style="color: var(--{color});">{ret_pct:+.2f}%</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">Benchmark: {metrics['benchmark_return']:.2f}%</div>
                    </div>
                """, unsafe_allow_html=True)
            with m_col2:
                st.markdown(f"""
                    <div class="terminal-card">
                        <div class="terminal-card-header">Sharpe / Sortino Ratio</div>
                        <div class="terminal-card-value">{metrics['sharpe']:.2f}</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">Sortino: {metrics['sortino']:.2f}</div>
                    </div>
                """, unsafe_allow_html=True)
            with m_col3:
                st.markdown(f"""
                    <div class="terminal-card">
                        <div class="terminal-card-header">Max Drawdown</div>
                        <div class="terminal-card-value" style="color: var(--red);">{metrics['max_drawdown']:.2f}%</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">Capital Safe: {100-metrics['max_drawdown']:.2f}%</div>
                    </div>
                """, unsafe_allow_html=True)
            with m_col4:
                st.markdown(f"""
                    <div class="terminal-card">
                        <div class="terminal-card-header">Win Rate / Trades</div>
                        <div class="terminal-card-value">{metrics['win_rate']:.1f}%</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">Total Trades: {metrics['trades_count']} | PF: {metrics['profit_factor']:.2f}</div>
                    </div>
                """, unsafe_allow_html=True)
                
            # Chart Section
            st.markdown("### Strategy Price & Signals Chart")
            
            # Detect buy/sell signals from position differences
            df_res = results['df']
            df_res['pos_diff'] = df_res['position'].diff()
            buy_sigs = df_res[df_res['pos_diff'] > 0]
            sell_sigs = df_res[df_res['pos_diff'] < 0]
            
            fig_price = plot_candlestick_chart(
                df_res, 
                selected_ticker, 
                buy_signals=buy_sigs, 
                sell_signals=sell_sigs, 
                chart_type="Candlestick" if chart_style == "Candlestick" else "Line"
            )
            st.plotly_chart(fig_price, use_container_width=True)
            
            st.markdown("### Performance Equity Curve")
            fig_equity = plot_equity_curve(df_res, strategy_type)
            st.plotly_chart(fig_equity, use_container_width=True)
            
            # Trades Table Log
            st.markdown("### Execution Trade Log")
            trades = results['trades']
            if trades:
                trades_df = pd.DataFrame(trades)
                trades_df = trades_df[["entry_date", "exit_date", "type", "entry_price", "exit_price", "pnl", "pnl_pct"]]
                
                html_rows = ""
                for _, row in trades_df.iterrows():
                    pnl_class = "trend-up" if row['pnl'] >= 0 else "trend-down"
                    pnl_arrow = "+" if row['pnl'] >= 0 else ""
                    
                    # Convert to selected currency
                    entry_formatted = format_currency(float(row['entry_price']))
                    exit_formatted = format_currency(float(row['exit_price']))
                    pnl_formatted = format_currency(abs(float(row['pnl'])))
                    
                    html_rows += f"""
                        <tr>
                            <td>{row['entry_date']}</td>
                            <td>{row['exit_date']}</td>
                            <td style="font-weight:bold; color: {'#29b6f6' if row['type'] == 'LONG' else '#ec4899'};">{row['type']}</td>
                            <td>{entry_formatted}</td>
                            <td>{exit_formatted}</td>
                            <td class="{pnl_class}">{pnl_arrow}{pnl_formatted}</td>
                            <td class="{pnl_class}">{row['pnl_pct']:+.2f}%</td>
                        </tr>
                    """
                
                st.markdown(f"""
                    <table class="styled-table">
                        <thead>
                            <tr>
                                <th>Entry Date</th>
                                <th>Exit Date</th>
                                <th>Type</th>
                                <th>Entry Price</th>
                                <th>Exit Price</th>
                                <th>Net PnL ({curr_symbol})</th>
                                <th>PnL (%)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {html_rows}
                        </tbody>
                    </table>
                """, unsafe_allow_html=True)
            else:
                st.info("No trades executed during this timeframe.")
else:
    st.info("💡 Set your strategy parameters in the main panels above and click 'Run Backtest Execution 🧪' to generate the reports.")
