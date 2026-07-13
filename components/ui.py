import os
import streamlit as st

def load_custom_css():
    """Reads custom stylesheet and injects it into streamlit app."""
    css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        st.warning("Stylesheet not found.")

def render_header(title: str, subtitle: str = None):
    """Renders a beautiful styled header."""
    if subtitle:
        st.markdown(f"""
            <div style='margin-bottom: 25px;'>
                <h1 class='terminal-title' style='margin: 0; font-size: 2.2rem;'>{title}</h1>
                <p style='color: var(--text-secondary); margin: 5px 0 0 0; font-size: 0.95rem;'>{subtitle}</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style='margin-bottom: 25px;'>
                <h1 class='terminal-title' style='margin: 0; font-size: 2.2rem;'>{title}</h1>
            </div>
        """, unsafe_allow_html=True)

def render_metric_card(title: str, value: str, change_pct: float, icon: str = ""):
    """Renders a high-fidelity quantitative terminal metric card."""
    trend_class = "trend-up" if change_pct >= 0 else "trend-down"
    trend_sign = "+" if change_pct >= 0 else ""
    icon_html = f"<span>{icon}</span>" if icon else ""
    
    st.markdown(f"""
        <div class="terminal-card">
            <div class="terminal-card-header">
                <span>{title}</span>
                {icon_html}
            </div>
            <div class="terminal-card-value">{value}</div>
            <div class="terminal-card-footer {trend_class}">
                <span>{trend_sign}{change_pct:.2f}%</span>
                <span style="font-weight: normal; color: var(--text-muted); margin-left: 5px;">(24h)</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_status_sidebar():
    """Renders a terminal system status on sidebar."""
    with st.sidebar:
        st.markdown("---")
        st.markdown("""
            <div style="padding: 10px; background-color: var(--bg-tertiary); border-radius: 8px; border: 1px solid var(--border);">
                <div style="display: flex; align-items: center; font-size: 0.8rem; font-weight: 600;">
                    <span class="status-dot"></span>
                    <span style="color: var(--text-primary);">QUANTLAB ENGINE ACTIVE</span>
                </div>
                <div style="margin-top: 8px; font-size: 0.7rem; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace;">
                    <span>SQLite Cache: <b>ONLINE</b></span><br/>
                    <span>Feed: <b>YAHOO FINANCE</b></span><br/>
                    <span>Platform: <b>Streamlit Local</b></span>
                </div>
            </div>
        """, unsafe_allow_html=True)

def format_currency(val_usd: float, symbol_only: bool = False) -> str:
    """Format USD value to USD ($) or INR (₹) depending on session state."""
    currency = st.session_state.get('currency', 'USD')
    if currency == 'INR':
        val_inr = val_usd * 83.0  # Static conversion rate for demonstration
        if symbol_only:
            return "₹"
        return f"₹{val_inr:,.2f}"
    else:
        if symbol_only:
            return "$"
        return f"${val_usd:,.2f}"

def render_currency_selector():
    """Renders the currency toggle in the sidebar."""
    if 'currency' not in st.session_state:
        st.session_state.currency = 'USD'
        
    st.sidebar.markdown("### Display Currency")
    currency = st.sidebar.radio(
        "Select Currency",
        options=["USD ($)", "INR (₹)"],
        index=0 if st.session_state.currency == 'USD' else 1,
        label_visibility="collapsed"
    )
    st.session_state.currency = 'USD' if "USD" in currency else 'INR'

def render_top_left_logo():
    """Put the website name on the top left corner of the page."""
    st.markdown("""
        <div style="position: absolute; top: -55px; left: 60px; z-index: 999999; display: flex; align-items: center;">
            <span style="font-weight: 800; font-size: 1.4rem; color: var(--accent); letter-spacing: -0.03em; text-shadow: 0 0 10px var(--accent-glow);">⚡ QuantLab</span>
        </div>
    """, unsafe_allow_html=True)

