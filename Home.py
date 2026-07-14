import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Import custom modules
from components.ui import load_custom_css, render_header, render_metric_card, render_status_sidebar, format_currency, render_currency_selector, render_top_left_logo, inject_html
from database.db_manager import get_watchlist, add_to_watchlist, remove_from_watchlist, get_backtest_history
from utils.data_loader import fetch_ticker_data, get_market_overview, search_ticker, fetch_multiple_tickers
from charts.terminal import plot_equity_curve

# Configure page
st.set_page_config(
    page_title="QuantLab Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
load_custom_css()

# Track Landing Splash state using a persistent file flag in the workspace
import os
STARTED_FLAG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".started_flag")

if 'started' not in st.session_state:
    st.session_state.started = os.path.exists(STARTED_FLAG_FILE)

# Landing Page
if not st.session_state.started:
    # Render splash landing page
    inject_html("<div style='height: 100px;'></div>")
    
    col_l1, col_l2, col_l3 = st.columns([1, 4, 1])
    with col_l2:
        inject_html("""
            <div style="text-align: center; background: linear-gradient(135deg, var(--bg-secondary) 0%, #121824 100%); padding: 50px; border-radius: 16px; border: 1px solid var(--border); box-shadow: 0 12px 40px rgba(0,0,0,0.5);">
                <div style="font-size: 4rem; margin-bottom: 10px;">⚡</div>
                <h1 style="font-size: 3.5rem; margin: 0; background: linear-gradient(90deg, #ffffff 0%, var(--accent) 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; letter-spacing: -0.04em; text-shadow: 0 0 30px var(--accent-glow);">QuantLab Terminal</h1>
                <p style="color: var(--text-secondary); font-size: 1.25rem; margin-top: 10px; margin-bottom: 40px; font-weight: 500;">
                    Commercial-Grade Quantitative Analysis & Backtesting workspace
                </p>
                <div style="text-align: left; max-width: 600px; margin: 0 auto 40px auto; color: var(--text-secondary); line-height: 1.8; font-size: 0.95rem;">
                    <div style="margin-bottom: 15px; display: flex; align-items: flex-start;">
                        <span style="color: var(--accent); margin-right: 12px; font-size: 1.2rem;">🧪</span>
                        <span><b>Strategy Backtesting Lab:</b> Design and simulate systematic trading rules (MA Crossover, RSI Reversion, Bollinger Bands) with dynamic slippage and commission settings.</span>
                    </div>
                    <div style="margin-bottom: 15px; display: flex; align-items: flex-start;">
                        <span style="color: var(--accent); margin-right: 12px; font-size: 1.2rem;">🛡️</span>
                        <span><b>Portfolio Risk Analytics:</b> Quantify portfolio tail risk using Value at Risk (VaR), Conditional VaR (CVaR), and project 252-day forward prices with Monte Carlo Brownian paths.</span>
                    </div>
                    <div style="margin-bottom: 15px; display: flex; align-items: flex-start;">
                        <span style="color: var(--accent); margin-right: 12px; font-size: 1.2rem;">🔍</span>
                        <span><b>Technical Scanner & HUD:</b> Analyze technical trends with real-time oscillators (RSI, MACD, ATR) overlaid on multi-pane candlestick charts.</span>
                    </div>
                </div>
            </div>
        """)
        
        # Center start button
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        btn_col1, btn_col2, btn_col3 = st.columns([1.5, 1, 1.5])
        with btn_col2:
            if st.button("GET STARTED ⚡", use_container_width=True, type="primary"):
                with open(STARTED_FLAG_FILE, "w") as f:
                    f.write("true")
                st.session_state.started = True
                st.rerun()

else:
    # Put website name top left logo
    render_top_left_logo()
    
    # Sidebar navigation info
    st.sidebar.markdown("""
        <div style='text-align: center; margin-bottom: 20px;'>
            <h2 style='margin: 0; color: var(--accent); font-size: 1.5rem;'>⚡ QuantLab</h2>
            <span style='color: var(--text-muted); font-size: 0.8rem;'>v1.0.0</span>
        </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("### Navigation")
    st.sidebar.markdown('<a href="/" target="_self" style="text-decoration:none; width:100%;"><div style="color:var(--text-primary); background-color:var(--bg-tertiary); border:1px solid var(--border); padding:10px 14px; border-radius:8px; display:flex; align-items:center; margin-bottom:8px; font-weight:600; box-shadow:0 4px 12px rgba(0,0,0,0.25);"><span style="margin-right:8px;">📊</span> Dashboard Overview</div></a>', unsafe_allow_html=True)
    st.sidebar.page_link("pages/01_Strategy_Lab.py", label="Strategy Lab", icon="🧪")
    st.sidebar.page_link("pages/02_Analytics_Risk.py", label="Analytics & Risk", icon="🛡️")
    st.sidebar.page_link("pages/03_Market_Scanner.py", label="Market Scanner", icon="🔍")

    # Currency selection
    render_currency_selector()
    
    # Diagnostics status sidebar
    render_status_sidebar()

    # Render header
    render_header("QuantLab Dashboard", "High-fidelity quantitative workspace & analytics terminal")

    # Fetch watchlists & index levels
    watchlist = get_watchlist()
    market_overview = get_market_overview()

    # Header Market Indices Ticker
    if market_overview:
        cols = st.columns(len(market_overview))
        for col, (symbol, data) in zip(cols, market_overview.items()):
            with col:
                trend_arrow = "▲" if data['change_pct'] >= 0 else "▼"
                trend_class = "trend-up" if data['change_pct'] >= 0 else "trend-down"
                
                # Convert index levels symbol based on currency if it represents pricing
                val_display = data['value']
                st.markdown(f"""
                    <div style="background-color: var(--bg-secondary); border: 1px solid var(--border); padding: 12px; border-radius: 8px; font-family: 'JetBrains Mono', monospace;">
                        <div style="color: var(--text-secondary); font-size: 0.75rem; text-transform: uppercase;">{data['name']}</div>
                        <div style="font-size: 1.2rem; font-weight: 700; margin: 4px 0;">{val_display:,.2f}</div>
                        <div class="{trend_class}" style="font-size: 0.8rem; font-weight: 600;">
                            {trend_arrow} {data['change']:+,.2f} ({data['change_pct']:.2f}%)
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Main Portfolio Metrics Row
    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_metric_card("Net Asset Value", format_currency(124538.92), 1.84, "💼")
    with metric_cols[1]:
        render_metric_card("Daily Profit/Loss", ("+" if 2253.12 >= 0 else "") + format_currency(2253.12), 2.15, "📈")
    with metric_cols[2]:
        render_metric_card("Sharpe Ratio (Roll)", "2.42", 0.50, "📊")
    with metric_cols[3]:
        render_metric_card("Value at Risk (95%)", format_currency(3124.50), -1.12, "🛡️")

    # Dashboard Content
    main_left, main_right = st.columns([1.5, 1])

    with main_left:
        st.markdown("### Interactive Watchlist")
        
        # Form to add new ticker with search resolver
        with st.expander("➕ Add Symbol to Watchlist"):
            search_query = st.text_input("Search Company Name or Keyword", placeholder="e.g. Apple, Microsoft, Reliance, Nvidia")
            if search_query:
                results = search_ticker(search_query)
                if results:
                    options = {f"{r['symbol']} - {r['name']}": r for r in results}
                    selected_opt = st.selectbox("Select Matching Symbol", options=list(options.keys()))
                    if st.button("Add Selected to Watchlist", use_container_width=True):
                        selected_item = options[selected_opt]
                        add_to_watchlist(selected_item['symbol'], selected_item['name'])
                        st.success(f"Added {selected_item['symbol']} to watchlist!")
                        st.rerun()
                else:
                    st.warning("No search matches found. Use direct input below.")
            
            st.markdown("<hr style='border-top:1px solid var(--border); margin:15px 0;'/>", unsafe_allow_html=True)
            direct_ticker = st.text_input("Or enter exact ticker directly", placeholder="e.g. AAPL, RELIANCE.NS").upper().strip()
            if st.button("Add Direct Ticker", use_container_width=True) and direct_ticker:
                try:
                    test_df = fetch_ticker_data(direct_ticker, (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"), datetime.now().strftime("%Y-%m-%d"))
                    if not test_df.empty:
                        add_to_watchlist(direct_ticker, f"{direct_ticker} Corp.")
                        st.success(f"{direct_ticker} added successfully!")
                        st.rerun()
                    else:
                        st.error(f"Could not load data for symbol {direct_ticker}")
                except Exception:
                    st.error("Error connecting to ticker service.")



        # Render Watchlist Cards/Rows
        if watchlist:
            watchlist_tickers = [item['ticker'] for item in watchlist]
            watchlist_dfs = fetch_multiple_tickers(watchlist_tickers)
            
            for idx, item in enumerate(watchlist):
                ticker = item['ticker']
                df_ticker = watchlist_dfs.get(ticker, pd.DataFrame())
                if not df_ticker.empty and len(df_ticker) >= 2:
                    last_price = df_ticker['close'].iloc[-1]
                    prev_price = df_ticker['close'].iloc[-2]
                    change = last_price - prev_price
                    change_pct = (change / prev_price) * 100
                    trend_class = "trend-up" if change_pct >= 0 else "trend-down"
                    trend_arrow = "▲" if change_pct >= 0 else "▼"
                    
                    wl_col1, wl_col2, wl_col3, wl_col4 = st.columns([1.5, 1.5, 1.5, 0.5])
                    with wl_col1:
                        st.markdown(f"""
                            <div style="padding: 10px 0;">
                                <span style="font-weight: 700; font-size: 1.1rem; color: var(--accent);">{ticker}</span><br/>
                                <span style="font-size: 0.75rem; color: var(--text-secondary);">{item['name']}</span>
                            </div>
                        """, unsafe_allow_html=True)
                    with wl_col2:
                        price_formatted = format_currency(float(last_price))
                        st.markdown(f"""
                            <div style="padding: 10px 0; font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 600;">
                                {price_formatted}
                            </div>
                        """, unsafe_allow_html=True)
                    with wl_col3:
                        st.markdown(f"""
                            <div class="{trend_class}" style="padding: 10px 0; font-family: 'JetBrains Mono', monospace; font-weight: 600;">
                                {trend_arrow} {change_pct:+.2f}%
                            </div>
                        """, unsafe_allow_html=True)
                    with wl_col4:
                        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                        if st.button("🗑️", key=f"del_{ticker}_{idx}"):
                            remove_from_watchlist(ticker)
                            st.success(f"Removed {ticker}!")
                            st.rerun()
                    st.markdown("<div style='border-bottom: 1px solid var(--border); margin: 5px 0;'></div>", unsafe_allow_html=True)
        else:
            st.info("Watchlist is currently empty. Add tickers above.")

    with main_right:
        st.markdown("### Recent Backtest Executions")
        history = get_backtest_history(limit=5)
        
        if history:
            for run in history:
                color_class = "trend-up" if run['total_return'] >= 0 else "trend-down"
                st.markdown(f"""
                    <div style="background-color: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 12px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: 700; color: var(--text-primary);">{run['ticker']} ({run['strategy']})</span>
                            <span style="font-size: 0.7rem; color: var(--text-muted);">{run['timestamp'][:16]}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-top: 8px; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">
                            <div>Return: <b class="{color_class}">{run['total_return']:+.2f}%</b></div>
                            <div>Sharpe: <b>{run['sharpe']:.2f}</b></div>
                            <div>Max DD: <b class="trend-down">{run['max_drawdown']:.2f}%</b></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent backtests. Head over to Strategy Lab to run one!")

    # Bottom area chart representing simulated index tracking portfolio
    st.markdown("### Portfolio Performance Performance Chart")
    default_port_df = fetch_ticker_data("SPY", "2025-01-01", "2026-07-01")
    if not default_port_df.empty:
        # Build simulated custom performance curve
        default_port_df['equity'] = default_port_df['close'] * 100000.0 / default_port_df['close'].iloc[0]
        fig = plot_equity_curve(default_port_df, "Passive SPY Index Tracker")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Historical index performance data unavailable.")
