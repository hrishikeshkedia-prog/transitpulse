"""
Real-time multi-symbol quote engine.
Uses yfinance fast_info (~0.14s/call) with parallel fetching and live polling.
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional

import pytz
import yfinance as yf

from core.global_markets import (
    detect_asset_type, get_exchange_info, get_market_status,
    get_currency_symbol, get_usd_rate,
)


@dataclass
class RealTimeQuote:
    symbol: str
    name: str = ""
    price: Optional[float] = None
    prev_close: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    open_: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[int] = None
    avg_volume: Optional[int] = None
    market_cap: Optional[float] = None
    currency: str = "USD"
    exchange: str = ""
    timezone: str = ""
    asset_type: str = "stock"
    year_high: Optional[float] = None
    year_low: Optional[float] = None
    pre_market_price: Optional[float] = None
    post_market_price: Optional[float] = None
    pre_market_change_pct: Optional[float] = None
    post_market_change_pct: Optional[float] = None
    last_updated: datetime = field(default_factory=datetime.now)
    market_status: str = "unknown"
    is_stale: bool = False
    error: Optional[str] = None
    # USD-converted price
    price_usd: Optional[float] = None
    usd_rate: Optional[float] = None

    @property
    def currency_symbol(self) -> str:
        return get_currency_symbol(self.currency)

    @property
    def age_seconds(self) -> float:
        return (datetime.now() - self.last_updated).total_seconds()

    @property
    def price_display(self) -> str:
        if self.price is None:
            return "N/A"
        sym = self.currency_symbol
        if self.currency in ("JPY", "KRW", "IDR"):
            return f"{sym}{self.price:,.0f}"
        return f"{sym}{self.price:,.2f}"

    @property
    def change_display(self) -> str:
        if self.change is None or self.change_pct is None:
            return "N/A"
        arrow = "▲" if self.change >= 0 else "▼"
        sym = self.currency_symbol
        if self.currency in ("JPY", "KRW", "IDR"):
            return f"{arrow} {sym}{abs(self.change):,.0f} ({self.change_pct:+.2f}%)"
        return f"{arrow} {sym}{abs(self.change):.2f} ({self.change_pct:+.2f}%)"


def _fetch_single(symbol: str) -> RealTimeQuote:
    """Fetch a single real-time quote using fast_info + supplemental info."""
    try:
        ticker = yf.Ticker(symbol)
        fi = ticker.fast_info

        price = getattr(fi, "last_price", None)
        prev_close = getattr(fi, "previous_close", None)
        open_ = getattr(fi, "open", None)
        high = getattr(fi, "day_high", None)
        low = getattr(fi, "day_low", None)
        volume = getattr(fi, "last_volume", None) or getattr(fi, "three_month_average_volume", None)
        avg_vol = getattr(fi, "three_month_average_volume", None)
        mkt_cap = getattr(fi, "market_cap", None)
        currency = getattr(fi, "currency", "USD") or "USD"
        exchange = getattr(fi, "exchange", "") or ""
        timezone = getattr(fi, "timezone", "") or ""
        year_high = getattr(fi, "year_high", None)
        year_low = getattr(fi, "year_low", None)

        # Change calculation
        change = None
        change_pct = None
        if price is not None and prev_close is not None and prev_close != 0:
            change = price - prev_close
            change_pct = (change / prev_close) * 100

        # Name from info (cached separately, may be slow - use shortName only)
        name = ""
        try:
            info = ticker.info
            name = info.get("shortName") or info.get("longName") or symbol
            # Pre/post market
            pre_price = info.get("preMarketPrice")
            post_price = info.get("postMarketPrice")
            pre_chg_pct = None
            post_chg_pct = None
            if pre_price and prev_close:
                pre_chg_pct = (pre_price / prev_close - 1) * 100
            if post_price and price:
                post_chg_pct = (post_price / price - 1) * 100
        except Exception:
            pre_price = None
            post_price = None
            pre_chg_pct = None
            post_chg_pct = None

        asset_type = detect_asset_type(symbol)
        market_status = get_market_status(symbol)

        # USD conversion
        usd_rate = get_usd_rate(currency)
        price_usd = price * usd_rate if (price and usd_rate) else price

        return RealTimeQuote(
            symbol=symbol,
            name=name,
            price=price,
            prev_close=prev_close,
            change=change,
            change_pct=change_pct,
            open_=open_,
            high=high,
            low=low,
            volume=int(volume) if volume else None,
            avg_volume=int(avg_vol) if avg_vol else None,
            market_cap=mkt_cap,
            currency=currency,
            exchange=exchange,
            timezone=timezone,
            asset_type=asset_type,
            year_high=year_high,
            year_low=year_low,
            pre_market_price=pre_price,
            post_market_price=post_price,
            pre_market_change_pct=pre_chg_pct,
            post_market_change_pct=post_chg_pct,
            last_updated=datetime.now(),
            market_status=market_status,
            is_stale=False,
            price_usd=price_usd,
            usd_rate=usd_rate,
        )

    except Exception as e:
        return RealTimeQuote(
            symbol=symbol,
            is_stale=True,
            error=str(e),
            last_updated=datetime.now(),
        )


def _fetch_single_fast(symbol: str) -> RealTimeQuote:
    """Ultra-fast quote using only fast_info (no info dict call). ~0.15s."""
    try:
        ticker = yf.Ticker(symbol)
        fi = ticker.fast_info

        price = getattr(fi, "last_price", None)
        prev_close = getattr(fi, "previous_close", None)
        open_ = getattr(fi, "open", None)
        high = getattr(fi, "day_high", None)
        low = getattr(fi, "day_low", None)
        volume = getattr(fi, "last_volume", None)
        avg_vol = getattr(fi, "three_month_average_volume", None)
        mkt_cap = getattr(fi, "market_cap", None)
        currency = getattr(fi, "currency", "USD") or "USD"
        exchange = getattr(fi, "exchange", "") or ""
        timezone = getattr(fi, "timezone", "") or ""
        year_high = getattr(fi, "year_high", None)
        year_low = getattr(fi, "year_low", None)

        change = None
        change_pct = None
        if price is not None and prev_close is not None and prev_close != 0:
            change = price - prev_close
            change_pct = (change / prev_close) * 100

        asset_type = detect_asset_type(symbol)
        market_status = get_market_status(symbol)

        usd_rate = 1.0 if currency == "USD" else None
        price_usd = price if currency == "USD" else None

        return RealTimeQuote(
            symbol=symbol,
            price=price,
            prev_close=prev_close,
            change=change,
            change_pct=change_pct,
            open_=open_,
            high=high,
            low=low,
            volume=int(volume) if volume else None,
            avg_volume=int(avg_vol) if avg_vol else None,
            market_cap=mkt_cap,
            currency=currency,
            exchange=exchange,
            timezone=timezone,
            asset_type=asset_type,
            year_high=year_high,
            year_low=year_low,
            last_updated=datetime.now(),
            market_status=market_status,
            is_stale=False,
            price_usd=price_usd,
            usd_rate=usd_rate,
        )
    except Exception as e:
        return RealTimeQuote(symbol=symbol, is_stale=True, error=str(e), last_updated=datetime.now())


def get_instant_quote(symbol: str) -> RealTimeQuote:
    """Full quote with name and pre/post market. ~0.5-1s."""
    return _fetch_single(symbol)


def get_instant_quote_fast(symbol: str) -> RealTimeQuote:
    """Ultra-fast quote (no name/pre-post lookup). ~0.15s."""
    return _fetch_single_fast(symbol)


def get_multi_quotes(symbols: List[str], fast: bool = True) -> Dict[str, RealTimeQuote]:
    """Fetch multiple quotes in parallel. fast=True skips name lookup."""
    fetch_fn = _fetch_single_fast if fast else _fetch_single
    results = {}
    with ThreadPoolExecutor(max_workers=min(len(symbols), 20)) as executor:
        future_map = {executor.submit(fetch_fn, sym): sym for sym in symbols}
        for future in as_completed(future_map):
            sym = future_map[future]
            try:
                results[sym] = future.result()
            except Exception as e:
                results[sym] = RealTimeQuote(symbol=sym, is_stale=True, error=str(e))
    return results


class QuoteFetcher:
    """
    Background polling quote fetcher for live dashboard.
    Refreshes a set of symbols at a configurable interval.
    """

    def __init__(self, symbols: List[str], refresh_interval: float = 5.0):
        self.symbols = list(symbols)
        self.refresh_interval = refresh_interval
        self._cache: Dict[str, RealTimeQuote] = {}
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._callbacks: List[Callable] = []

    def get_cached(self, symbol: str) -> Optional[RealTimeQuote]:
        with self._lock:
            return self._cache.get(symbol)

    def get_all_cached(self) -> Dict[str, RealTimeQuote]:
        with self._lock:
            return dict(self._cache)

    def refresh_now(self):
        """Synchronously fetch all symbols and update cache."""
        new_quotes = get_multi_quotes(self.symbols, fast=True)
        with self._lock:
            self._cache.update(new_quotes)
        for cb in self._callbacks:
            try:
                cb(new_quotes)
            except Exception:
                pass

    def add_callback(self, cb: Callable):
        self._callbacks.append(cb)

    def start_polling(self):
        """Start background polling thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop_polling(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=self.refresh_interval + 2)

    def _poll_loop(self):
        while self._running:
            self.refresh_now()
            time.sleep(self.refresh_interval)

    def add_symbol(self, symbol: str):
        if symbol not in self.symbols:
            self.symbols.append(symbol)

    def remove_symbol(self, symbol: str):
        self.symbols = [s for s in self.symbols if s != symbol]
        with self._lock:
            self._cache.pop(symbol, None)
