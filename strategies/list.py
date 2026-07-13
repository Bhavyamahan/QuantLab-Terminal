import pandas as pd
from indicators.technicals import compute_sma, compute_rsi, compute_bollinger_bands

def run_ma_crossover_strategy(df: pd.DataFrame, fast_period: int = 10, slow_period: int = 30) -> pd.DataFrame:
    """
    Fast SMA crossing Slow SMA strategy.
    Returns df with a 'signal' column (1 = Long, -1 = Short/Exit, 0 = Flat/Hold)
    """
    df = df.copy()
    df['fast_ma'] = compute_sma(df, fast_period)
    df['slow_ma'] = compute_sma(df, slow_period)
    
    df['signal'] = 0
    # Buy signal when fast > slow
    df.loc[df['fast_ma'] > df['slow_ma'], 'signal'] = 1
    # Sell signal when fast <= slow
    df.loc[df['fast_ma'] <= df['slow_ma'], 'signal'] = -1
    
    # Create target position
    df['position'] = df['signal'].shift(1).fillna(0)
    return df

def run_rsi_reversion_strategy(df: pd.DataFrame, rsi_period: int = 14, oversold: float = 30, overbought: float = 70) -> pd.DataFrame:
    """
    RSI Overbought / Oversold mean reversion strategy.
    """
    df = df.copy()
    df['rsi'] = compute_rsi(df, rsi_period)
    
    df['position'] = 0.0
    current_pos = 0.0
    positions = []
    
    for i in range(len(df)):
        rsi_val = df['rsi'].iloc[i]
        if pd.isna(rsi_val):
            positions.append(0.0)
            continue
            
        if rsi_val < oversold:
            current_pos = 1.0  # Buy
        elif rsi_val > overbought:
            current_pos = -1.0  # Short / Exit
            
        positions.append(current_pos)
        
    df['position'] = positions
    df['position'] = df['position'].shift(1).fillna(0)
    return df

def run_bb_breakout_strategy(df: pd.DataFrame, period: int = 20, num_std: int = 2) -> pd.DataFrame:
    """
    Bollinger Bands breakout strategy.
    """
    df = df.copy()
    upper, middle, lower = compute_bollinger_bands(df, period, num_std)
    df['bb_upper'] = upper
    df['bb_lower'] = lower
    
    df['position'] = 0.0
    current_pos = 0.0
    positions = []
    
    for i in range(len(df)):
        close_val = df['close'].iloc[i]
        lower_val = df['bb_lower'].iloc[i]
        upper_val = df['bb_upper'].iloc[i]
        
        if pd.isna(lower_val) or pd.isna(upper_val):
            positions.append(0.0)
            continue
            
        if close_val < lower_val:
            current_pos = 1.0  # Buy
        elif close_val > upper_val:
            current_pos = -1.0  # Short / Exit
            
        positions.append(current_pos)
        
    df['position'] = positions
    df['position'] = df['position'].shift(1).fillna(0)
    return df
