import pandas as pd
import numpy as np
from analytics.risk_metrics import calculate_sharpe_ratio, calculate_sortino_ratio, calculate_max_drawdown

def run_backtest(df: pd.DataFrame, initial_capital: float = 100000.0, fee_pct: float = 0.001) -> dict:
    """
    Backtesting engine that parses standard strategy positions (long: 1, short/flat: -1/0)
    and computes transaction costs, equity curve, trade logs, and metrics.
    """
    df = df.copy().reset_index(drop=True)
    if 'position' not in df.columns:
        raise ValueError("DataFrame must contain a 'position' column indicating desired holdings.")
        
    prices = df['close'].values
    positions = df['position'].values
    dates = df['date'].values
    
    cash = initial_capital
    holdings = 0.0
    equity = []
    trades = []
    
    last_position = 0.0
    
    for i in range(len(df)):
        price = prices[i]
        target_pos = positions[i]
        date = dates[i]
        
        # Check if we need to trade
        if target_pos != last_position:
            # We want to change position. Sell current holdings, buy new position
            # 1. Close current position
            if last_position != 0.0:
                pnl = (price - entry_price) * holdings if last_position > 0 else (entry_price - price) * abs(holdings)
                pnl_pct = (pnl / (entry_price * abs(holdings))) * 100 if holdings != 0 else 0.0
                
                # Add to cash
                trade_val = abs(holdings) * price
                transaction_fee = trade_val * fee_pct
                
                if last_position > 0:
                    cash += holdings * price - transaction_fee
                else:
                    cash += (entry_price * abs(holdings)) + pnl - transaction_fee
                    
                trades.append({
                    "exit_date": pd.to_datetime(date).strftime("%Y-%m-%d"),
                    "ticker": df.get('ticker', ['ASSET'])[0] if 'ticker' in df.columns else 'ASSET',
                    "type": "LONG" if last_position > 0 else "SHORT",
                    "entry_date": pd.to_datetime(entry_date).strftime("%Y-%m-%d"),
                    "entry_price": float(entry_price),
                    "exit_price": float(price),
                    "pnl": float(pnl - transaction_fee),
                    "pnl_pct": float(pnl_pct - (fee_pct * 2 * 100)) # Approx fee impact
                })
                holdings = 0.0
                
            # 2. Open new position
            if target_pos != 0.0:
                entry_price = price
                entry_date = date
                
                # Use all cash for long/short
                transaction_fee = cash * fee_pct
                usable_cash = cash - transaction_fee
                holdings = usable_cash / price if target_pos > 0 else -usable_cash / price
                
                # Adjust cash balance
                if target_pos > 0:
                    cash -= (holdings * price) + transaction_fee
                else:
                    # For short, we keep the cash and keep track of entry liabilities
                    cash -= transaction_fee
                    
            last_position = target_pos
            
        # Calculate current equity
        curr_equity = cash
        if last_position > 0:
            curr_equity += holdings * price
        elif last_position < 0:
            # Short position valuation
            pnl = (entry_price - price) * abs(holdings)
            curr_equity += (entry_price * abs(holdings)) + pnl
            
        equity.append(curr_equity)
        
    df['equity'] = equity
    df['returns'] = df['equity'].pct_change().fillna(0.0)
    
    # Calculate performance metrics
    total_return = ((equity[-1] / initial_capital) - 1.0) * 100
    returns_series = df['returns']
    
    # Sharpe and Sortino
    sharpe = calculate_sharpe_ratio(returns_series)
    sortino = calculate_sortino_ratio(returns_series)
    max_dd = calculate_max_drawdown(df['equity']) * 100 # In percentage
    
    # Win rate and trades count
    trades_df = pd.DataFrame(trades)
    if not trades_df.empty:
        win_rate = (trades_df['pnl'] > 0).mean() * 100
        total_wins = trades_df[trades_df['pnl'] > 0]['pnl'].sum()
        total_losses = abs(trades_df[trades_df['pnl'] < 0]['pnl'].sum())
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
    else:
        win_rate = 0.0
        profit_factor = 1.0
        
    # Benchmark Returns (Buy & Hold)
    benchmark_return = ((prices[-1] / prices[0]) - 1.0) * 100
    
    metrics = {
        "initial_capital": initial_capital,
        "final_equity": equity[-1],
        "total_return": total_return,
        "benchmark_return": benchmark_return,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_dd,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "trades_count": len(trades)
    }
    
    return {
        "df": df,
        "metrics": metrics,
        "trades": trades
    }
