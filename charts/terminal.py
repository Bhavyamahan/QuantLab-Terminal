import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def apply_terminal_theme(fig):
    """Applies high-end dark finance terminal theme to any Plotly figure."""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color='#8e9cae', size=11),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.03)',
            linecolor='rgba(255,255,255,0.08)',
            showline=True,
            showgrid=True,
            mirror=True
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.03)',
            linecolor='rgba(255,255,255,0.08)',
            showline=True,
            showgrid=True,
            mirror=True
        ),
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            font=dict(size=10)
        )
    )
    return fig

def plot_candlestick_chart(df: pd.DataFrame, ticker: str, buy_signals=None, sell_signals=None, chart_type: str = "Candlestick") -> go.Figure:
    """Generates a professional multi-pane chart with Price, EMAs, Volume, and Technical Signals."""
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05, 
        row_heights=[0.75, 0.25]
    )
    
    # 1. Price Plot
    if chart_type == "Candlestick":
        fig.add_trace(
            go.Candlestick(
                x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name=ticker,
                increasing_line_color='#00e676',
                decreasing_line_color='#ff1744',
                increasing_fillcolor='rgba(0, 230, 118, 0.25)',
                decreasing_fillcolor='rgba(255, 23, 68, 0.25)',
                line_width=1.5
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['close'],
                mode='lines',
                line=dict(color='#29b6f6', width=2),
                name=ticker
            ),
            row=1, col=1
        )
    
    # Buy/Sell markers if provided
    if buy_signals is not None and not buy_signals.empty:
        fig.add_trace(
            go.Scatter(
                x=buy_signals['date'],
                y=buy_signals['close'] * 0.98,
                mode='markers',
                marker=dict(symbol='triangle-up', size=11, color='#00e676', line=dict(width=1, color='white')),
                name='Buy Signal'
            ),
            row=1, col=1
        )
        
    if sell_signals is not None and not sell_signals.empty:
        fig.add_trace(
            go.Scatter(
                x=sell_signals['date'],
                y=sell_signals['close'] * 1.02,
                mode='markers',
                marker=dict(symbol='triangle-down', size=11, color='#ff1744', line=dict(width=1, color='white')),
                name='Sell Signal'
            ),
            row=1, col=1
        )
    
    # 2. Volume
    colors = ['#00e676' if row['close'] >= row['open'] else '#ff1744' for _, row in df.iterrows()]
    fig.add_trace(
        go.Bar(
            x=df['date'],
            y=df['volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.4
        ),
        row=2, col=1
    )
    
    fig.update_layout(xaxis_rangeslider_visible=False)
    apply_terminal_theme(fig)
    fig.update_layout(height=450, title_text=f"{ticker} Technical Chart")
    return fig

def plot_equity_curve(equity_df: pd.DataFrame, strategy_name: str) -> go.Figure:
    """Plots the equity curve comparisons (Strategy vs Benchmark)."""
    fig = go.Figure()
    
    # Normalize benchmark
    benchmark_start = equity_df['close'].iloc[0]
    normalized_benchmark = (equity_df['close'] / benchmark_start) * equity_df['equity'].iloc[0]
    
    fig.add_trace(
        go.Scatter(
            x=equity_df['date'],
            y=equity_df['equity'],
            mode='lines',
            line=dict(color='#29b6f6', width=2),
            name=f"Strategy: {strategy_name}",
            fill='tozeroy',
            fillcolor='rgba(41, 182, 246, 0.05)'
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=equity_df['date'],
            y=normalized_benchmark,
            mode='lines',
            line=dict(color='#8e9cae', width=1.5, dash='dash'),
            name="Benchmark (Buy & Hold)"
        )
    )
    
    apply_terminal_theme(fig)
    fig.update_layout(height=350, title_text="Performance Over Time")
    return fig
