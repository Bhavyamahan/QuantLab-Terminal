import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

from components.ui import load_custom_css, render_header, render_status_sidebar, render_currency_selector, render_top_left_logo, format_currency

from database.db_manager import get_watchlist
from utils.data_loader import fetch_ticker_data
from indicators.technicals import (
    compute_sma, compute_ema, compute_rsi, 
    compute_macd, compute_bollinger_bands, compute_atr
)
from charts.terminal import plot_candlestick_chart, apply_terminal_theme

st.set_page_config(page_title="Market Scanner | QuantLab", page_icon="🔍", layout="wide")
load_custom_css()
render_top_left_logo()
render_status_sidebar()
render_currency_selector()

st.sidebar.markdown("### Navigation")
st.sidebar.markdown('<a href="/" target="_self" style="text-decoration:none; width:100%;"><div style="color:var(--text-primary); background-color:var(--bg-tertiary); border:1px solid var(--border); padding:10px 14px; border-radius:8px; display:flex; align-items:center; margin-bottom:8px; font-weight:600; box-shadow:0 4px 12px rgba(0,0,0,0.25);"><span style="margin-right:8px;">📊</span> Dashboard Overview</div></a>', unsafe_allow_html=True)
st.sidebar.page_link("pages/01_Strategy_Lab.py", label="Strategy Lab", icon="🧪")
st.sidebar.page_link("pages/02_Analytics_Risk.py", label="Analytics & Risk", icon="🛡️")
st.sidebar.page_link("pages/03_Market_Scanner.py", label="Market Scanner", icon="🔍")

render_header("Market Scanner & Technical Terminal", "Real-time technical indicators, oscillator panels, and trading signal detection")

watchlist_items = get_watchlist()
ticker_options = [item['ticker'] for item in watchlist_items] if watchlist_items else ["AAPL", "MSFT", "TSLA"]

# Top Selection Bar
scan_col1, scan_col2, scan_col3, scan_col4 = st.columns([1.5, 1, 1, 1])
with scan_col1:
    selected_asset = st.selectbox("Select Asset to Scan", options=ticker_options)
with scan_col2:
    start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=180))
with scan_col3:
    end_date = st.date_input("End Date", value=datetime.now())
with scan_col4:
    chart_style = st.selectbox("Chart Type", options=["Candlestick", "Line Graph"])

if selected_asset:
    with st.spinner(f"Computing technical feeds for {selected_asset}..."):
        df = fetch_ticker_data(selected_asset, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        
        if df.empty or len(df) < 20:
            st.error("Insufficient market data for this period.")
        else:
            # Compute technical values
            df['sma_20'] = compute_sma(df, 20)
            df['ema_10'] = compute_ema(df, 10)
            df['rsi_14'] = compute_rsi(df, 14)
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = compute_bollinger_bands(df, 20, 2)
            df['macd_line'], df['macd_signal'], df['macd_hist'] = compute_macd(df, 12, 26, 9)
            df['atr_14'] = compute_atr(df, 14)
            
            # Generate buy/sell signals based on simple RSI/BB crossovers
            # Let's show these on the main candlestick chart
            buy_signals = df[(df['rsi_14'] < 30) | (df['close'] < df['bb_lower'])]
            sell_signals = df[(df['rsi_14'] > 70) | (df['close'] > df['bb_upper'])]
            
            # Technical Indicators HUD
            st.markdown("### Technical Indicators HUD")
            last_row = df.iloc[-1]
            
            hud_col1, hud_col2, hud_col3, hud_col4 = st.columns(4)
            with hud_col1:
                rsi_val = last_row['rsi_14']
                if rsi_val < 30:
                    rsi_status = "Oversold 🟢"
                elif rsi_val > 70:
                    rsi_status = "Overbought 🔴"
                else:
                    rsi_status = "Neutral ⚪"
                st.markdown(f"""
                    <div class="terminal-card">
                        <div class="terminal-card-header">RSI (14)</div>
                        <div class="terminal-card-value">{rsi_val:.2f}</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">Signal: <b>{rsi_status}</b></div>
                    </div>
                """, unsafe_allow_html=True)
                
            with hud_col2:
                macd_val = last_row['macd_line']
                sig_val = last_row['macd_signal']
                macd_status = "Bullish Crossover 🟢" if macd_val > sig_val else "Bearish Crossover 🔴"
                st.markdown(f"""
                    <div class="terminal-card">
                        <div class="terminal-card-header">MACD (12, 26, 9)</div>
                        <div class="terminal-card-value">{macd_val:.2f}</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">Signal: <b>{macd_status}</b></div>
                    </div>
                """, unsafe_allow_html=True)
                
            with hud_col3:
                close = last_row['close']
                lower = last_row['bb_lower']
                upper = last_row['bb_upper']
                if close < lower:
                    bb_status = "Price < Lower Band 🟢"
                elif close > upper:
                    bb_status = "Price > Upper Band 🔴"
                else:
                    bb_status = "Inside Bands ⚪"
                
                close_formatted = format_currency(float(close))
                lower_formatted = format_currency(float(lower))
                upper_formatted = format_currency(float(upper))
                
                st.markdown(f"""
                    <div class="terminal-card">
                        <div class="terminal-card-header">Bollinger Bands (20, 2)</div>
                        <div class="terminal-card-value">{close_formatted}</div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary);">Bands: <b>{lower_formatted} - {upper_formatted}</b> ({bb_status})</div>
                    </div>
                """, unsafe_allow_html=True)
                
            with hud_col4:
                atr_val = last_row['atr_14']
                atr_formatted = format_currency(float(atr_val))
                st.markdown(f"""
                    <div class="terminal-card">
                        <div class="terminal-card-header">Volatility (ATR 14)</div>
                        <div class="terminal-card-value">{atr_formatted}</div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">Expected Daily Range</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Interactive Plotly Chart
            fig = plot_candlestick_chart(df, selected_asset, buy_signals, sell_signals, chart_type="Candlestick" if chart_style == "Candlestick" else "Line")
            
            # Overlay Bollinger Bands and SMA
            fig.add_trace(
                go.Scatter(x=df['date'], y=df['bb_upper'], mode='lines', line=dict(color='rgba(255,255,255,0.15)', width=1, dash='dash'), name='BB Upper')
            )
            fig.add_trace(
                go.Scatter(x=df['date'], y=df['bb_lower'], mode='lines', line=dict(color='rgba(255,255,255,0.15)', width=1, dash='dash'), name='BB Lower')
            )
            fig.add_trace(
                go.Scatter(x=df['date'], y=df['sma_20'], mode='lines', line=dict(color='#29b6f6', width=1.5), name='SMA 20')
            )
            
            st.plotly_chart(fig, use_container_width=True)
