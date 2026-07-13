import pandas as pd
import numpy as np

def compute_sma(df: pd.DataFrame, period: int = 20, column: str = 'close') -> pd.Series:
    return df[column].rolling(window=period).mean()

def compute_ema(df: pd.DataFrame, period: int = 20, column: str = 'close') -> pd.Series:
    return df[column].ewm(span=period, adjust=False).mean()

def compute_rsi(df: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
    delta = df[column].diff()
    gain = (delta.where(delta > 0, 0)).copy()
    loss = (-delta.where(delta < 0, 0)).copy()
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # First rsi calculations
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    # Wilder's smoothing technique
    for i in range(period, len(df)):
        avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period - 1) + loss.iloc[i]) / period
        
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_macd(df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, column: str = 'close') -> tuple:
    fast_ema = compute_ema(df, fast_period, column)
    slow_ema = compute_ema(df, slow_period, column)
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def compute_bollinger_bands(df: pd.DataFrame, period: int = 20, num_std: int = 2, column: str = 'close') -> tuple:
    middle_band = compute_sma(df, period, column)
    std_dev = df[column].rolling(window=period).std()
    upper_band = middle_band + (num_std * std_dev)
    lower_band = middle_band - (num_std * std_dev)
    return upper_band, middle_band, lower_band

def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    # Wilders smoothing
    for i in range(period, len(df)):
        atr.iloc[i] = (atr.iloc[i-1] * (period - 1) + tr.iloc[i]) / period
        
    return atr
