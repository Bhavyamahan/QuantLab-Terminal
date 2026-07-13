import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialize SQLite database schemas."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Watchlist table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            ticker TEXT PRIMARY KEY,
            name TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Backtest history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS backtest_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            strategy_name TEXT,
            start_date TEXT,
            end_date TEXT,
            total_return REAL,
            sharpe_ratio REAL,
            max_drawdown REAL,
            win_rate REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Seed default watchlist if empty
    cursor.execute("SELECT COUNT(*) FROM watchlist")
    if cursor.fetchone()[0] == 0:
        default_tickers = [
            ("AAPL", "Apple Inc."),
            ("MSFT", "Microsoft Corporation"),
            ("TSLA", "Tesla Inc."),
            ("NVDA", "NVIDIA Corporation"),
            ("AMZN", "Amazon.com, Inc.")
        ]
        cursor.executemany("INSERT INTO watchlist (ticker, name) VALUES (?, ?)", default_tickers)
        
    conn.commit()
    conn.close()

def get_watchlist():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ticker, name FROM watchlist ORDER BY added_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"ticker": r[0], "name": r[1]} for r in rows]

def add_to_watchlist(ticker: str, name: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO watchlist (ticker, name) VALUES (?, ?)", (ticker.upper(), name))
        conn.commit()
    except Exception as e:
        print(f"Error adding to watchlist: {e}")
    finally:
        conn.close()

def remove_from_watchlist(ticker: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker.upper(),))
    conn.commit()
    conn.close()

def log_backtest(ticker: str, strategy: str, start: str, end: str, metrics: dict):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO backtest_history 
            (ticker, strategy_name, start_date, end_date, total_return, sharpe_ratio, max_drawdown, win_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker.upper(),
            strategy,
            start,
            end,
            metrics.get("total_return", 0.0),
            metrics.get("sharpe", 0.0),
            metrics.get("max_drawdown", 0.0),
            metrics.get("win_rate", 0.0)
        ))
        conn.commit()
    except Exception as e:
        print(f"Error logging backtest: {e}")
    finally:
        conn.close()

def get_backtest_history(limit: int = 5):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ticker, strategy_name, start_date, end_date, total_return, sharpe_ratio, max_drawdown, win_rate, timestamp
        FROM backtest_history 
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{
        "ticker": r[0],
        "strategy": r[1],
        "start": r[2],
        "end": r[3],
        "total_return": r[4],
        "sharpe": r[5],
        "max_drawdown": r[6],
        "win_rate": r[7],
        "timestamp": r[8]
    } for r in rows]

# Initialize tables
init_db()
