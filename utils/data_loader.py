import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta

@st.cache_data(ttl=3600)  # Cache data for 1 hour to avoid rate limits
def fetch_ticker_data(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetch historical daily data for a single stock ticker using yfinance.
    """
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            return pd.DataFrame()
        
        # Reset index to make Date a column
        data = data.reset_index()
        
        # Clean column names (yfinance sometimes returns multi-index or Capitalized columns)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]
            
        data.columns = [col.lower() for col in data.columns]
        
        # Ensure date column is datetime
        data['date'] = pd.to_datetime(data['date'])
        data = data.sort_values('date').reset_index(drop=True)
        
        # Ensure numeric types
        for col in ['open', 'high', 'low', 'close', 'adj close', 'volume']:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
                
        # Fill missing values
        data = data.ffill().bfill()
        
        return data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)  # Cache watchlist prices for 5 mins
def fetch_multiple_tickers(tickers: list) -> dict:
    """
    Fetch historical daily data for multiple stock tickers in parallel.
    """
    if not tickers:
        return {}
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=10)
        data = yf.download(tickers, start=start_date, end=end_date, group_by='ticker', progress=False)
        
        result = {}
        for ticker in tickers:
            if len(tickers) == 1:
                df = data
            else:
                try:
                    df = data[ticker]
                except KeyError:
                    continue
            
            if not df.empty:
                df = df.dropna().reset_index()
                df.columns = [col.lower() for col in df.columns]
                result[ticker] = df
        return result
    except Exception as e:
        print(f"Error fetching multiple tickers: {e}")
        return {}

@st.cache_data(ttl=900)  # Cache market info for 15 mins
def get_market_overview() -> dict:
    """
    Fetch current market status/indices in parallel.
    """
    indices = {
        "^GSPC": "S&P 500",
        "^IXIC": "Nasdaq Composite",
        "^DJI": "Dow Jones",
        "^VIX": "CBOE Volatility Index"
    }
    
    overview = {}
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=10)
    
    try:
        data = yf.download(list(indices.keys()), start=start_date, end=end_date, group_by='ticker', progress=False)
        for symbol, name in indices.items():
            if len(indices) == 1:
                df = data
            else:
                try:
                    df = data[symbol]
                except KeyError:
                    continue
            
            if not df.empty:
                df = df.dropna().reset_index()
                df.columns = [col.lower() for col in df.columns]
                if len(df) >= 2:
                    last_row = df.iloc[-1]
                    prev_row = df.iloc[-2]
                    
                    close_val = float(last_row['close'])
                    prev_close = float(prev_row['close'])
                    change = close_val - prev_close
                    change_pct = (change / prev_close) * 100
                    
                    sparkline_vals = df['close'].tail(5).tolist()
                    
                    overview[symbol] = {
                        "name": name,
                        "value": close_val,
                        "change": change,
                        "change_pct": change_pct,
                        "sparkline": sparkline_vals
                    }
    except Exception as e:
        print(f"Error fetching market overview: {e}")
    return overview

import requests

LOCAL_TICKER_CATALOG = [
    {"symbol": "AAPL", "name": "Apple Inc."},
    {"symbol": "MSFT", "name": "Microsoft Corporation"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation"},
    {"symbol": "AMZN", "name": "Amazon.com Inc."},
    {"symbol": "META", "name": "Meta Platforms Inc."},
    {"symbol": "GOOGL", "name": "Alphabet Inc."},
    {"symbol": "TSLA", "name": "Tesla Inc."},
    {"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust"},
    {"symbol": "QQQ", "name": "Invesco QQQ Trust"},
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries Limited"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services Limited"},
    {"symbol": "INFY.NS", "name": "Infosys Limited"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank Limited"},
]


def _local_ticker_search(query: str) -> list:
    normalized = query.strip().lower()
    return [
        item
        for item in LOCAL_TICKER_CATALOG
        if normalized in item["symbol"].lower() or normalized in item["name"].lower()
    ][:8]


@st.cache_data(ttl=3600)
def search_ticker(query: str) -> list:
    """
    Search ticker symbol by name/keyword using Yahoo Finance API.
    Returns a list of dicts: [{'symbol': 'AAPL', 'name': 'Apple Inc.'}, ...]
    """
    if not query or len(query.strip()) < 2:
        return []
    local_results = _local_ticker_search(query)
    if local_results:
        return local_results
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            quotes = data.get("quotes", [])
            results = []
            for q in quotes:
                symbol = q.get("symbol")
                name = q.get("shortname") or q.get("longname") or symbol
                # Filter to only keep relevant symbols (stocks/ETFs/indices)
                quote_type = q.get("quoteType", "")
                if symbol and quote_type in ["EQUITY", "ETF", "INDEX"]:
                    results.append({"symbol": symbol, "name": name})
            return results
    except Exception as e:
        print(f"Error searching ticker: {e}")
    return []
