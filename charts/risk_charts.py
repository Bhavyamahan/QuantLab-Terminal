import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from charts.terminal import apply_terminal_theme

def plot_correlation_heatmap(corr_matrix: pd.DataFrame) -> go.Figure:
    """Generates a premium correlation matrix heatmap."""
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        colorscale='RdBu',
        zmin=-1.0,
        zmax=1.0,
        hoverongaps=False,
        colorbar=dict(title="Correlation", thickness=15, len=0.8)
    ))
    
    apply_terminal_theme(fig)
    fig.update_layout(
        height=350, 
        title_text="Asset Correlation Matrix",
        margin=dict(l=40, r=40, t=40, b=40)
    )
    return fig

def plot_monte_carlo(sim_prices: np.ndarray, dates=None) -> go.Figure:
    """Plots Monte Carlo projection trajectories and confidence percentiles."""
    days, sims = sim_prices.shape
    fig = go.Figure()
    
    x_axis = np.arange(days)
    
    # Calculate percentiles
    p10 = np.percentile(sim_prices, 10, axis=1)
    p50 = np.percentile(sim_prices, 50, axis=1)
    p90 = np.percentile(sim_prices, 90, axis=1)
    
    # Draw sample simulation paths (first 50 paths for visual clarity)
    for i in range(min(50, sims)):
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=sim_prices[:, i],
                mode='lines',
                line=dict(color='rgba(255, 255, 255, 0.05)', width=1),
                showlegend=False
            )
        )
        
    # Overlap percentiles
    fig.add_trace(
        go.Scatter(
            x=x_axis,
            y=p90,
            mode='lines',
            line=dict(color='#00e676', width=2, dash='dot'),
            name='90th Percentile (Optimistic)'
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=x_axis,
            y=p50,
            mode='lines',
            line=dict(color='#29b6f6', width=2.5),
            name='50th Percentile (Median)'
        )
    )
    
    fig.add_trace(
        go.Scatter(
            x=x_axis,
            y=p10,
            mode='lines',
            line=dict(color='#ff1744', width=2, dash='dot'),
            name='10th Percentile (Pessimistic)'
        )
    )
    
    apply_terminal_theme(fig)
    fig.update_layout(
        height=380,
        title_text="Monte Carlo 252-Day Price Projection",
        xaxis_title="Days Forward",
        yaxis_title="Projected Close Price"
    )
    return fig

def plot_drawdown_chart(prices: pd.Series) -> go.Figure:
    """Plots a filled area chart of historic drawdowns."""
    roll_max = prices.cummax()
    drawdown = (prices - roll_max) / roll_max * 100
    
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=prices.index,
            y=drawdown,
            mode='lines',
            line=dict(color='#ff1744', width=1.5),
            fill='tozeroy',
            fillcolor='rgba(255, 23, 68, 0.1)',
            name='Drawdown'
        )
    )
    
    apply_terminal_theme(fig)
    fig.update_layout(
        height=250,
        title_text="Underwater Drawdown (%)",
        yaxis_title="Percent"
    )
    return fig
