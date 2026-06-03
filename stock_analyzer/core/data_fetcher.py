import json
import pickle
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

from config import DATA_DIR, CACHE_EXPIRY_HOURS


class DataFetcher:
    """Fetches and caches stock data with retry logic."""

    def __init__(self):
        self.cache_dir = DATA_DIR / "cache"
        self.cache_dir.mkdir(exist_ok=True)

    def _cache_path(self, key: str) -> Path:
        safe = key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe}.pkl"

    def _is_cache_valid(self, path: Path) -> bool:
        if not path.exists():
            return False
        age = time.time() - path.stat().st_mtime
        return age < CACHE_EXPIRY_HOURS * 3600

    def _load_cache(self, key: str) -> Optional[Any]:
        path = self._cache_path(key)
        if self._is_cache_valid(path):
            try:
                with open(path, "rb") as f:
                    return pickle.load(f)
            except Exception:
                return None
        return None

    def _save_cache(self, key: str, data: Any) -> None:
        path = self._cache_path(key)
        try:
            with open(path, "wb") as f:
                pickle.dump(data, f)
        except Exception:
            pass

    def get_ticker(self, symbol: str) -> yf.Ticker:
        return yf.Ticker(symbol.upper())

    def get_price_history(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        cache_key = f"history_{symbol}_{period}_{interval}"
        if not force_refresh:
            cached = self._load_cache(cache_key)
            if cached is not None:
                return cached

        ticker = self.get_ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=True)

        if df.empty:
            raise ValueError(f"No price data found for {symbol}")

        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        df.columns = [c.lower() for c in df.columns]
        df = df[["open", "high", "low", "close", "volume"]].dropna()
        df = df.sort_index()

        self._save_cache(cache_key, df)
        return df

    def get_info(self, symbol: str, force_refresh: bool = False) -> Dict:
        cache_key = f"info_{symbol}"
        if not force_refresh:
            cached = self._load_cache(cache_key)
            if cached is not None:
                return cached

        ticker = self.get_ticker(symbol)
        info = ticker.info or {}
        self._save_cache(cache_key, info)
        return info

    def get_financials(self, symbol: str) -> Dict[str, pd.DataFrame]:
        cache_key = f"financials_{symbol}"
        cached = self._load_cache(cache_key)
        if cached is not None:
            return cached

        ticker = self.get_ticker(symbol)
        data = {
            "income_stmt": ticker.income_stmt,
            "balance_sheet": ticker.balance_sheet,
            "cash_flow": ticker.cash_flow,
            "quarterly_income": ticker.quarterly_income_stmt,
            "quarterly_balance": ticker.quarterly_balance_sheet,
            "quarterly_cash_flow": ticker.quarterly_cash_flow,
        }
        self._save_cache(cache_key, data)
        return data

    def get_options_chain(self, symbol: str) -> Optional[Dict]:
        ticker = self.get_ticker(symbol)
        try:
            expirations = ticker.options
            if not expirations:
                return None
            result = {"expirations": list(expirations), "chains": {}}
            for exp in expirations[:3]:
                chain = ticker.option_chain(exp)
                result["chains"][exp] = {
                    "calls": chain.calls,
                    "puts": chain.puts,
                }
            return result
        except Exception:
            return None

    def get_news(self, symbol: str) -> List[Dict]:
        cache_key = f"news_{symbol}"
        cached = self._load_cache(cache_key)
        if cached is not None:
            return cached

        ticker = self.get_ticker(symbol)
        try:
            raw_news = ticker.news or []
            # yfinance >=0.2.x nests data under 'content'
            news = []
            for item in raw_news:
                content = item.get("content", {})
                if content:
                    canonical = {
                        "title": content.get("title", ""),
                        "publisher": (content.get("provider") or {}).get("displayName", ""),
                        "link": content.get("canonicalUrl", {}).get("url", ""),
                        "providerPublishTime": None,
                        "summary": content.get("summary", ""),
                    }
                    pub_date = content.get("pubDate", "")
                    if pub_date:
                        try:
                            from datetime import datetime, timezone
                            dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                            canonical["providerPublishTime"] = int(dt.timestamp())
                        except Exception:
                            pass
                    news.append(canonical)
                else:
                    news.append(item)
        except Exception:
            news = []
        self._save_cache(cache_key, news)
        return news

    def get_multiple_histories(
        self, symbols: List[str], period: str = "1y"
    ) -> Dict[str, pd.DataFrame]:
        results = {}
        for sym in symbols:
            try:
                results[sym] = self.get_price_history(sym, period=period)
            except Exception:
                pass
        return results

    def get_market_benchmarks(self, period: str = "1y") -> Dict[str, pd.DataFrame]:
        benchmarks = {
            "S&P 500": "^GSPC",
            "NASDAQ": "^IXIC",
            "DOW": "^DJI",
            "VIX": "^VIX",
            "10Y Treasury": "^TNX",
        }
        results = {}
        for name, sym in benchmarks.items():
            try:
                results[name] = self.get_price_history(sym, period=period)
            except Exception:
                pass
        return results

    def search_symbol(self, query: str) -> List[Dict]:
        try:
            results = yf.Search(query, max_results=10)
            return results.quotes if hasattr(results, "quotes") else []
        except Exception:
            return []

    def get_sector_etfs(self) -> Dict[str, str]:
        return {
            "XLK": "Technology",
            "XLF": "Financials",
            "XLV": "Healthcare",
            "XLE": "Energy",
            "XLY": "Consumer Disc.",
            "XLP": "Consumer Staples",
            "XLI": "Industrials",
            "XLB": "Materials",
            "XLRE": "Real Estate",
            "XLU": "Utilities",
            "XLC": "Communication",
        }
