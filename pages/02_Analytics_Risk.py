import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from components.ui import load_custom_css, render_header, render_status_sidebar, render_currency_selector, render_top_left_logo

from database.db_manager import get_watchlist
from utils.data_loader import fetch_ticker_data
from analytics.risk_metrics import calculate_returns, calculate_var_cvar, calculate_beta, run_monte_carlo
from charts.risk_charts import plot_correlation_heatmap, plot_monte_carlo, plot_drawdown_chart

st.set_page_config(page_title="Analytics & Risk | QuantLab", page_icon="🛡️", layout="wide")
load_custom_css()
render_top_left_logo()
render_status_sidebar()
render_currency_selector()

st.sidebar.markdown("### Navigation")
st.sidebar.markdown('<a href="/" target="_self" style="text-decoration:none; width:100%;"><div style="color:var(--text-primary); background-color:var(--bg-tertiary); border:1px solid var(--border); padding:10px 14px; border-radius:8px; display:flex; align-items:center; margin-bottom:8px; font-weight:600; box-shadow:0 4px 12px rgba(0,0,0,0.25);"><span style="margin-right:8px;">📊</span> Dashboard Overview</div></a>', unsafe_allow_html=True)
st.sidebar.page_link("pages/01_Strategy_Lab.py", label="Strategy Lab", icon="🧪")
st.sidebar.page_link("pages/02_Analytics_Risk.py", label="Analytics & Risk", icon="🛡️")
st.sidebar.page_link("pages/03_Market_Scanner.py", label="Market Scanner", icon="🔍")

render_header("Portfolio Analytics & Risk Lab", "Quantitative risk metrics, correlation matrices, and predictive Monte Carlo forecasts")

watchlist_items = get_watchlist()
default_symbols = [item['ticker'] for item in watchlist_items] if watchlist_items else ["AAPL", "MSFT", "TSLA", "NVDA", "AMZN"]

# Asset Selection Controls
st.markdown("### Portfolio Risk Settings")
col_s1, col_s2 = st.columns([3, 1])
with col_s1:
    selected_assets = st.multiselect(
        "Select Portfolio Assets", 
        options=default_symbols, 
        default=default_symbols[:3] if len(default_symbols) >= 3 else default_symbols
    )
with col_s2:
    confidence_lvl = st.slider("VaR Confidence Level (%)", min_value=90.0, max_value=99.0, value=95.0, step=1.0) / 100.0

if len(selected_assets) < 1:
    st.warning("Please select at least one asset to analyze.")
else:
    with st.spinner("Analyzing portfolio risk profiles..."):
        # Load asset data for last 2 years
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)
        
        returns_dict = {}
        prices_dict = {}
        
        for ticker in selected_assets:
            df = fetch_ticker_data(ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
            if not df.empty:
                returns_dict[ticker] = calculate_returns(df, 'close')
                prices_dict[ticker] = df.set_index('date')['close']
                
        # Build returns and correlation tables
        returns_df = pd.DataFrame(returns_dict).dropna()
        prices_df = pd.DataFrame(prices_dict).dropna()
        
        if returns_df.empty:
            st.error("Could not retrieve sufficient overlapping historical dates for selected assets.")
        else:
            # Render Portfolio risk cards
            # We assume an equal-weight portfolio
            weights = np.ones(len(selected_assets)) / len(selected_assets)
            portfolio_returns = returns_df.dot(weights)
            
            p_var, p_cvar = calculate_var_cvar(portfolio_returns, confidence_lvl)
            
            # Fetch SPY for market Beta benchmark
            spy_df = fetch_ticker_data("SPY", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
            p_beta = 1.0
            if not spy_df.empty:
                spy_returns = calculate_returns(spy_df, 'close')
                p_beta = calculate_beta(portfolio_returns, spy_returns)
                
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.markdown(f"""
                    <div class="terminal-card">
                        <div class="terminal-card-header">Value at Risk (VaR)</div>
                        <div class="terminal-card-value" style="color: var(--red);">{p_var * 100:.2f}%</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">Max daily loss confidence</div>
                        <p style="font-size: 0.7rem; color: var(--text-muted); margin-top: 8px; line-height: 1.2;">
                            <b>Definition:</b> The maximum expected loss (percentage of portfolio) over a 1-day period at a {confidence_lvl*100:.0f}% confidence level.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            with col_m2:
                st.markdown(f"""
                    <div class="terminal-card">
                        <div class="terminal-card-header">Conditional VaR (CVaR)</div>
                        <div class="terminal-card-value" style="color: var(--red);">{p_cvar * 100:.2f}%</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">Average tail risk losses</div>
                        <p style="font-size: 0.7rem; color: var(--text-muted); margin-top: 8px; line-height: 1.2;">
                            <b>Definition:</b> The average loss expected on days when losses break past the VaR threshold (worst-case tail scenarios).
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            with col_m3:
                st.markdown(f"""
                    <div class="terminal-card">
                        <div class="terminal-card-header">Portfolio Beta</div>
                        <div class="terminal-card-value">{p_beta:.2f}</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">Relative to S&P 500</div>
                        <p style="font-size: 0.7rem; color: var(--text-muted); margin-top: 8px; line-height: 1.2;">
                            <b>Definition:</b> Volatility relative to the market benchmark (S&P 500). Beta > 1.0 means the asset fluctuates more than the market.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            with col_m4:
                vol = portfolio_returns.std() * np.sqrt(252) * 100
                st.markdown(f"""
                    <div class="terminal-card">
                        <div class="terminal-card-header">Annual Volatility</div>
                        <div class="terminal-card-value">{vol:.2f}%</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">Rolling 2-year sigma</div>
                        <p style="font-size: 0.7rem; color: var(--text-muted); margin-top: 8px; line-height: 1.2;">
                            <b>Definition:</b> Annualized standard deviation of daily returns. Indicates general volatility and price instability.
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
            # Heatmaps and Drawdown row
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                corr_matrix = returns_df.corr()
                st.plotly_chart(plot_correlation_heatmap(corr_matrix), use_container_width=True)
            with col_g2:
                # Plot Drawdown of equal weighted portfolio
                # Calculate synthetic portfolio price index
                port_prices = (1 + portfolio_returns).cumprod() * 100
                st.plotly_chart(plot_drawdown_chart(port_prices), use_container_width=True)
                
            # Monte Carlo Section
            st.markdown("### Monte Carlo Forecasts")
            mc_col1, mc_col2 = st.columns([1, 3])
            with mc_col1:
                target_sim_asset = st.selectbox("Select Asset to Project", options=selected_assets)
                num_simulations = st.number_input("Paths Count", min_value=50, max_value=2000, value=500, step=50)
                projection_days = st.number_input("Forward Days", min_value=10, max_value=504, value=252)
                
                run_mc = st.button("Generate Projections", use_container_width=True, type="primary")
            
            with mc_col2:
                if run_mc:
                    with st.spinner("Generating Monte Carlo simulation paths..."):
                        asset_prices = prices_df[target_sim_asset]
                        simulations = run_monte_carlo(asset_prices, projection_days, num_simulations)
                        fig_mc = plot_monte_carlo(simulations)
                        st.plotly_chart(fig_mc, use_container_width=True)
                else:
                    st.info("Configure parameters and click 'Generate Projections' to run forecasted Brownian paths.")
