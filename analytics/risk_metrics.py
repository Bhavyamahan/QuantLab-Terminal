import numpy as np
import pandas as pd
from scipy.stats import norm

def calculate_returns(df: pd.DataFrame, column: str = 'close') -> pd.Series:
    return df[column].pct_change().dropna()

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02, trading_days: int = 252) -> float:
    if len(returns) == 0:
        return 0.0
    daily_rf = risk_free_rate / trading_days
    excess_returns = returns - daily_rf
    mean_excess = excess_returns.mean()
    std_dev = returns.std()
    if std_dev == 0 or np.isnan(std_dev):
        return 0.0
    return (mean_excess / std_dev) * np.sqrt(trading_days)

def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.02, trading_days: int = 252) -> float:
    if len(returns) == 0:
        return 0.0
    daily_rf = risk_free_rate / trading_days
    excess_returns = returns - daily_rf
    mean_excess = excess_returns.mean()
    
    # Calculate downside standard deviation
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std()
    if downside_std == 0 or np.isnan(downside_std) or len(downside_returns) == 0:
        return 0.0
    return (mean_excess / downside_std) * np.sqrt(trading_days)

def calculate_max_drawdown(prices: pd.Series) -> float:
    if len(prices) == 0:
        return 0.0
    roll_max = prices.cummax()
    drawdown = (prices - roll_max) / roll_max
    return float(drawdown.min())

def calculate_var_cvar(returns: pd.Series, confidence_level: float = 0.95) -> tuple:
    """
    Returns (Value at Risk, Conditional Value at Risk) using Historical Simulation.
    """
    if len(returns) == 0:
        return 0.0, 0.0
    
    sorted_returns = np.sort(returns)
    cutoff_idx = int((1 - confidence_level) * len(sorted_returns))
    
    if cutoff_idx == 0:
        cutoff_idx = 1
        
    var = -sorted_returns[cutoff_idx]
    cvar = -sorted_returns[:cutoff_idx].mean()
    
    return float(var), float(cvar)

def calculate_beta(stock_returns: pd.Series, market_returns: pd.Series) -> float:
    """
    Calculate asset Beta relative to market index returns.
    """
    # Align dates
    combined = pd.concat([stock_returns, market_returns], axis=1).dropna()
    if len(combined) < 5:
        return 1.0
    
    cov = np.cov(combined.iloc[:, 0], combined.iloc[:, 1])
    market_var = cov[1, 1]
    
    if market_var == 0:
        return 1.0
        
    beta = cov[0, 1] / market_var
    return float(beta)

def run_monte_carlo(prices: pd.Series, days: int = 252, simulations: int = 500) -> np.ndarray:
    """
    Run Monte Carlo simulation using Geometric Brownian Motion.
    Returns: ndarray of shape (days, simulations) of projected prices.
    """
    if len(prices) < 2:
        return np.zeros((days, simulations))
        
    returns = prices.pct_change().dropna()
    mu = returns.mean()
    sigma = returns.std()
    
    # Make sure volatility isn't zero
    if sigma == 0 or np.isnan(sigma):
        sigma = 0.01
        
    dt = 1 # 1 day step
    last_price = prices.iloc[-1]
    
    # Generate drift and shock
    drift = (mu - 0.5 * sigma**2) * dt
    shock = sigma * np.sqrt(dt)
    
    sim_prices = np.zeros((days, simulations))
    sim_prices[0] = last_price
    
    for t in range(1, days):
        random_shocks = np.random.normal(0, 1, simulations)
        sim_prices[t] = sim_prices[t-1] * np.exp(drift + shock * random_shocks)
        
    return sim_prices
