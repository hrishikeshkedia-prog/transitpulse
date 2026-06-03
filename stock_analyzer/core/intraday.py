"""
Intraday analysis engine: 1m/5m/15m/30m/60m data, VWAP, volume profile,
opening range, intraday patterns, and session statistics.
"""
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import pytz
import yfinance as yf
from datetime import datetime, timedelta


VALID_INTERVALS = {"1m": 7, "2m": 60, "5m": 60, "15m": 60, "30m": 60, "60m": 730, "90m": 60}


def get_intraday_data(
    symbol: str,
    interval: str = "5m",
    days: int = 2,
) -> pd.DataFrame:
    """
    Fetch intraday OHLCV data from yfinance.
    Returns timezone-naive UTC DataFrame with normalized columns.
    """
    if interval not in VALID_INTERVALS:
        interval = "5m"

    max_days = VALID_INTERVALS[interval]
    days = min(days, max_days)

    ticker = yf.Ticker(symbol)

    if interval == "1m":
        period = f"{min(days, 7)}d"
    else:
        period = f"{days}d"

    df = ticker.history(period=period, interval=interval, auto_adjust=True)

    if df.empty:
        return df

    df.index = pd.to_datetime(df.index)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    df.columns = [c.lower() for c in df.columns]
    df = df[["open", "high", "low", "close", "volume"]].dropna()
    df = df.sort_index()
    return df


def intraday_vwap(df: pd.DataFrame) -> pd.Series:
    """
    VWAP computed for each trading session (resets at midnight).
    """
    typical = (df["high"] + df["low"] + df["close"]) / 3
    # Group by date for intraday reset
    dates = df.index.normalize()
    vwap_vals = pd.Series(np.nan, index=df.index)

    for date in dates.unique():
        mask = dates == date
        sub = df[mask]
        tp = typical[mask]
        cum_tpv = (tp * sub["volume"]).cumsum()
        cum_vol = sub["volume"].cumsum()
        vwap_vals[mask] = cum_tpv / cum_vol.replace(0, np.nan)

    return vwap_vals


def intraday_vwap_bands(df: pd.DataFrame, vwap: pd.Series, n_stds: int = 2) -> Dict[str, pd.Series]:
    """VWAP + standard deviation bands."""
    typical = (df["high"] + df["low"] + df["close"]) / 3
    dates = df.index.normalize()
    std_vals = pd.Series(np.nan, index=df.index)

    for date in dates.unique():
        mask = dates == date
        tp_deviation = (typical[mask] - vwap[mask]) ** 2
        cum_variance = (tp_deviation * df["volume"][mask]).cumsum() / df["volume"][mask].cumsum().replace(0, np.nan)
        std_vals[mask] = np.sqrt(cum_variance)

    bands = {}
    for n in range(1, n_stds + 1):
        bands[f"upper_{n}"] = vwap + n * std_vals
        bands[f"lower_{n}"] = vwap - n * std_vals
    return bands


def intraday_levels(df: pd.DataFrame, prev_df: Optional[pd.DataFrame] = None) -> Dict:
    """
    Compute key intraday price levels:
    - Opening price, overnight gap
    - Session high/low
    - VWAP and bands
    - Previous day OHLC pivot points
    - Opening range (first 30 candles of session)
    """
    if df.empty:
        return {}

    # Today's session
    today_date = df.index[-1].date()
    today_mask = df.index.date == today_date
    today = df[today_mask]

    result = {
        "current_price": float(df["close"].iloc[-1]),
        "session_open": float(today["open"].iloc[0]) if not today.empty else None,
        "session_high": float(today["high"].max()) if not today.empty else None,
        "session_low": float(today["low"].min()) if not today.empty else None,
        "session_volume": int(today["volume"].sum()) if not today.empty else None,
    }

    # Previous session data
    prev_dates = sorted(df.index.date)
    if len(prev_dates) >= 2:
        prev_date = [d for d in prev_dates if d != today_date]
        if prev_date:
            prev_date = prev_date[-1]
            prev_mask = df.index.date == prev_date
            prev_session = df[prev_mask]
            if not prev_session.empty:
                prev_close = float(prev_session["close"].iloc[-1])
                prev_high = float(prev_session["high"].max())
                prev_low = float(prev_session["low"].min())
                prev_open = float(prev_session["open"].iloc[0])

                result["prev_close"] = prev_close
                result["prev_high"] = prev_high
                result["prev_low"] = prev_low
                result["prev_open"] = prev_open

                # Gap calculation
                session_open = result.get("session_open")
                if session_open and prev_close:
                    result["gap_pct"] = (session_open / prev_close - 1) * 100
                    result["gap_type"] = "up" if result["gap_pct"] > 0 else "down" if result["gap_pct"] < 0 else "flat"

                # Classic pivot points
                pivot = (prev_high + prev_low + prev_close) / 3
                result["pivot"] = pivot
                result["r1"] = 2 * pivot - prev_low
                result["s1"] = 2 * pivot - prev_high
                result["r2"] = pivot + (prev_high - prev_low)
                result["s2"] = pivot - (prev_high - prev_low)
                result["r3"] = prev_high + 2 * (pivot - prev_low)
                result["s3"] = prev_low - 2 * (prev_high - pivot)

    # VWAP
    vwap = intraday_vwap(df)
    result["vwap"] = float(vwap.iloc[-1]) if not vwap.empty else None

    # Opening range (first 30 minutes)
    if not today.empty and len(today) >= 6:
        or_bars = today.head(min(6, len(today)))  # ~30min at 5m
        result["or_high"] = float(or_bars["high"].max())
        result["or_low"] = float(or_bars["low"].min())
        result["or_mid"] = (result["or_high"] + result["or_low"]) / 2

    return result


def intraday_volume_profile(df: pd.DataFrame, bins: int = 20) -> pd.DataFrame:
    """
    Build a volume profile histogram (price bins × volume).
    Returns DataFrame with: price_mid, volume, pct_of_total, is_poc, is_va.
    """
    if df.empty:
        return pd.DataFrame()

    price_min = df["low"].min()
    price_max = df["high"].max()
    bin_size = (price_max - price_min) / bins

    profile = []
    total_vol = df["volume"].sum()

    for i in range(bins):
        bin_low = price_min + i * bin_size
        bin_high = bin_low + bin_size
        bin_mid = (bin_low + bin_high) / 2
        mask = (df["close"] >= bin_low) & (df["close"] < bin_high)
        vol = df.loc[mask, "volume"].sum()
        profile.append({"price_low": bin_low, "price_high": bin_high,
                        "price_mid": bin_mid, "volume": vol})

    result = pd.DataFrame(profile)
    if result.empty or total_vol == 0:
        return result

    result["pct_of_total"] = result["volume"] / total_vol * 100
    result = result.sort_values("volume", ascending=False)

    # Point of Control (highest volume)
    poc_price = result.iloc[0]["price_mid"]
    result["is_poc"] = result["price_mid"] == poc_price

    # Value Area (70% of volume)
    target = total_vol * 0.70
    sorted_by_price = result.sort_values("price_mid")
    poc_idx = sorted_by_price["volume"].idxmax()
    va_volume = sorted_by_price.loc[poc_idx, "volume"]
    va_indices = [poc_idx]

    above = sorted_by_price.index[sorted_by_price.index > poc_idx].tolist()
    below = sorted_by_price.index[sorted_by_price.index < poc_idx].tolist()[::-1]
    a_ptr, b_ptr = 0, 0

    while va_volume < target and (a_ptr < len(above) or b_ptr < len(below)):
        a_vol = sorted_by_price.loc[above[a_ptr], "volume"] if a_ptr < len(above) else 0
        b_vol = sorted_by_price.loc[below[b_ptr], "volume"] if b_ptr < len(below) else 0
        if a_vol >= b_vol and a_ptr < len(above):
            va_volume += a_vol
            va_indices.append(above[a_ptr])
            a_ptr += 1
        elif b_ptr < len(below):
            va_volume += b_vol
            va_indices.append(below[b_ptr])
            b_ptr += 1
        else:
            break

    result["is_va"] = result.index.isin(va_indices)
    va_rows = result[result["is_va"]]
    if not va_rows.empty:
        result.attrs["va_high"] = va_rows["price_high"].max()
        result.attrs["va_low"] = va_rows["price_low"].min()
        result.attrs["poc"] = poc_price

    return result.sort_values("price_mid", ascending=False)


def detect_intraday_patterns(df: pd.DataFrame, levels: Dict) -> List[Dict]:
    """Detect intraday trading patterns and setups."""
    patterns = []
    if df.empty or len(df) < 5:
        return patterns

    current = float(df["close"].iloc[-1])
    vwap = levels.get("vwap")
    or_high = levels.get("or_high")
    or_low = levels.get("or_low")
    gap_pct = levels.get("gap_pct", 0)
    gap_type = levels.get("gap_type", "flat")

    # Gap analysis
    if abs(gap_pct or 0) > 1.0:
        patterns.append({
            "name": f"Gap {'Up' if gap_pct > 0 else 'Down'} ({abs(gap_pct):.1f}%)",
            "direction": "bullish" if gap_pct > 0 else "bearish",
            "description": f"Significant {'upward' if gap_pct > 0 else 'downward'} gap from previous close",
        })

    # VWAP analysis
    if vwap:
        dist = (current / vwap - 1) * 100
        if current > vwap:
            if dist > 2:
                patterns.append({"name": "Extended Above VWAP", "direction": "bearish",
                                  "description": f"Price is {dist:.1f}% above VWAP — potential mean reversion"})
            else:
                patterns.append({"name": "Above VWAP", "direction": "bullish",
                                  "description": f"Price holding above VWAP (+{dist:.1f}%) — bullish bias"})
        else:
            if dist < -2:
                patterns.append({"name": "Extended Below VWAP", "direction": "bullish",
                                  "description": f"Price is {abs(dist):.1f}% below VWAP — potential bounce"})
            else:
                patterns.append({"name": "Below VWAP", "direction": "bearish",
                                  "description": f"Price below VWAP ({dist:.1f}%) — bearish bias"})

    # Opening range breakout
    if or_high and or_low:
        if current > or_high:
            patterns.append({"name": "ORB Breakout (Long)", "direction": "bullish",
                              "description": f"Price broke above opening range high ${or_high:.2f}"})
        elif current < or_low:
            patterns.append({"name": "ORB Breakdown (Short)", "direction": "bearish",
                              "description": f"Price broke below opening range low ${or_low:.2f}"})

    # Volume spike
    if len(df) >= 20:
        vol_avg = df["volume"].rolling(20).mean().iloc[-1]
        vol_now = df["volume"].iloc[-1]
        if vol_avg and vol_now > 2 * vol_avg:
            patterns.append({"name": f"Volume Spike ({vol_now/vol_avg:.1f}x)", "direction": "neutral",
                              "description": "Unusually high volume — potential institutional activity"})

    # Trend for session
    if len(df) >= 10:
        session_start = df["close"].iloc[0]
        session_chg = (current / session_start - 1) * 100
        recent_5 = df["close"].tail(5)
        recent_trend = (recent_5.iloc[-1] / recent_5.iloc[0] - 1) * 100

        if abs(session_chg) > 2:
            direction = "bullish" if session_chg > 0 else "bearish"
            patterns.append({"name": f"Strong Session {'Up' if session_chg > 0 else 'Down'}trend",
                              "direction": direction,
                              "description": f"Session change: {session_chg:+.1f}%"})

        if abs(recent_trend) > 1 and (session_chg * recent_trend < 0):
            patterns.append({"name": "Intraday Reversal", "direction": "neutral",
                              "description": f"Recent 5-bar trend ({recent_trend:+.1f}%) reversing session direction"})

    # Pivot bounces
    for label, price_val in [("R1", levels.get("r1")), ("S1", levels.get("s1")),
                              ("Pivot", levels.get("pivot"))]:
        if price_val:
            dist = abs(current / price_val - 1) * 100
            if dist < 0.3:
                direction = "neutral"
                if label.startswith("R"):
                    direction = "bearish"
                elif label.startswith("S"):
                    direction = "bullish"
                patterns.append({"name": f"At {label} Level", "direction": direction,
                                  "description": f"Price testing pivot {label} at ${price_val:.2f}"})

    return patterns


def analyze_intraday(symbol: str, interval: str = "5m") -> Dict:
    """Full intraday analysis report for a symbol."""
    df = get_intraday_data(symbol, interval=interval, days=3)

    if df.empty:
        return {"error": f"No intraday data available for {symbol}"}

    today_date = df.index[-1].date()
    today_mask = df.index.date == today_date
    today_df = df[today_mask]

    levels = intraday_levels(df)
    vwap = intraday_vwap(df)
    vwap_bands = intraday_vwap_bands(df, vwap)
    volume_profile = intraday_volume_profile(today_df if not today_df.empty else df)
    patterns = detect_intraday_patterns(today_df if not today_df.empty else df, levels)

    # Session statistics
    if not today_df.empty:
        session_open = float(today_df["open"].iloc[0])
        session_close = float(today_df["close"].iloc[-1])
        session_chg = (session_close / session_open - 1) * 100
        session_vol = int(today_df["volume"].sum())
        bars_traded = len(today_df)
    else:
        session_open = session_close = session_chg = session_vol = bars_traded = None

    # Technical on intraday data
    intraday_indicators = {}
    if len(today_df) >= 14:
        from core.technical import rsi, macd, atr
        try:
            intraday_indicators["rsi"] = float(rsi(today_df).iloc[-1])
        except Exception:
            pass
        try:
            m = macd(today_df)
            intraday_indicators["macd_hist"] = float(m["histogram"].iloc[-1])
        except Exception:
            pass
        try:
            intraday_indicators["atr"] = float(atr(today_df).iloc[-1])
            if session_close and intraday_indicators["atr"]:
                intraday_indicators["atr_pct"] = intraday_indicators["atr"] / session_close * 100
        except Exception:
            pass

    # Intraday high/low with times
    if not today_df.empty:
        high_idx = today_df["high"].idxmax()
        low_idx = today_df["low"].idxmin()
        session_high_time = str(high_idx.time()) if hasattr(high_idx, "time") else str(high_idx)
        session_low_time = str(low_idx.time()) if hasattr(low_idx, "time") else str(low_idx)
    else:
        session_high_time = session_low_time = None

    poc = volume_profile.attrs.get("poc") if not volume_profile.empty else None
    va_high = volume_profile.attrs.get("va_high") if not volume_profile.empty else None
    va_low = volume_profile.attrs.get("va_low") if not volume_profile.empty else None

    return {
        "symbol": symbol,
        "interval": interval,
        "date": str(today_date),
        "total_bars": len(df),
        "session_bars": bars_traded,
        "session_open": session_open,
        "session_close": session_close,
        "session_change_pct": session_chg,
        "session_high": levels.get("session_high"),
        "session_low": levels.get("session_low"),
        "session_high_time": session_high_time,
        "session_low_time": session_low_time,
        "session_volume": session_vol,
        "levels": levels,
        "vwap": float(vwap.iloc[-1]) if not vwap.empty else None,
        "vwap_bands": {k: float(v.iloc[-1]) for k, v in vwap_bands.items() if not v.empty},
        "volume_profile": volume_profile,
        "poc": poc,
        "va_high": va_high,
        "va_low": va_low,
        "patterns": patterns,
        "intraday_indicators": intraday_indicators,
        "df": df,
        "today_df": today_df,
    }
