"""
Chart pattern detection: candlestick patterns and classical chart formations.
"""
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


def _is_green(row) -> bool:
    return row["close"] > row["open"]


def _is_red(row) -> bool:
    return row["close"] < row["open"]


def _body_size(row) -> float:
    return abs(row["close"] - row["open"])


def _upper_shadow(row) -> float:
    return row["high"] - max(row["open"], row["close"])


def _lower_shadow(row) -> float:
    return min(row["open"], row["close"]) - row["low"]


def detect_candlestick_patterns(df: pd.DataFrame) -> List[Dict]:
    """Detect candlestick patterns in the last 5 candles."""
    patterns = []
    if len(df) < 5:
        return patterns

    c = df.tail(5).reset_index(drop=True)

    def add(name, direction, desc):
        patterns.append({"name": name, "direction": direction, "description": desc, "date": str(df.index[-1].date() if hasattr(df.index[-1], 'date') else df.index[-1])})

    last = c.iloc[-1]
    prev = c.iloc[-2]
    two_ago = c.iloc[-3]

    # Doji
    body = _body_size(last)
    total_range = last["high"] - last["low"]
    if total_range > 0 and body / total_range < 0.1:
        add("Doji", "neutral", "Indecision candle — market equilibrium")

    # Hammer
    if _is_green(last) and _lower_shadow(last) >= 2 * body and _upper_shadow(last) < body:
        add("Hammer", "bullish", "Potential reversal after downtrend")

    # Hanging Man
    if _is_red(last) and _lower_shadow(last) >= 2 * body and _upper_shadow(last) < body:
        add("Hanging Man", "bearish", "Potential reversal after uptrend")

    # Inverted Hammer / Shooting Star
    if _upper_shadow(last) >= 2 * body and _lower_shadow(last) < body:
        if _is_green(last):
            add("Inverted Hammer", "bullish", "Potential bullish reversal")
        else:
            add("Shooting Star", "bearish", "Potential bearish reversal")

    # Engulfing
    if _is_green(last) and _is_red(prev) and last["close"] > prev["open"] and last["open"] < prev["close"]:
        add("Bullish Engulfing", "bullish", "Strong bullish reversal signal")

    if _is_red(last) and _is_green(prev) and last["open"] > prev["close"] and last["close"] < prev["open"]:
        add("Bearish Engulfing", "bearish", "Strong bearish reversal signal")

    # Morning Star
    if (
        _is_red(two_ago)
        and _body_size(prev) < _body_size(two_ago) * 0.3
        and _is_green(last)
        and last["close"] > (two_ago["open"] + two_ago["close"]) / 2
    ):
        add("Morning Star", "bullish", "Three-candle bullish reversal pattern")

    # Evening Star
    if (
        _is_green(two_ago)
        and _body_size(prev) < _body_size(two_ago) * 0.3
        and _is_red(last)
        and last["close"] < (two_ago["open"] + two_ago["close"]) / 2
    ):
        add("Evening Star", "bearish", "Three-candle bearish reversal pattern")

    # Three White Soldiers
    if all(_is_green(c.iloc[i]) for i in [-3, -2, -1]) and c.iloc[-1]["close"] > c.iloc[-2]["close"] > c.iloc[-3]["close"]:
        add("Three White Soldiers", "bullish", "Strong bullish continuation pattern")

    # Three Black Crows
    if all(_is_red(c.iloc[i]) for i in [-3, -2, -1]) and c.iloc[-1]["close"] < c.iloc[-2]["close"] < c.iloc[-3]["close"]:
        add("Three Black Crows", "bearish", "Strong bearish continuation pattern")

    # Piercing Line
    if _is_red(prev) and _is_green(last):
        midpoint = (prev["open"] + prev["close"]) / 2
        if last["open"] < prev["close"] and last["close"] > midpoint:
            add("Piercing Line", "bullish", "Bullish reversal — pierces into prior red candle")

    # Dark Cloud Cover
    if _is_green(prev) and _is_red(last):
        midpoint = (prev["open"] + prev["close"]) / 2
        if last["open"] > prev["close"] and last["close"] < midpoint:
            add("Dark Cloud Cover", "bearish", "Bearish reversal — covers into prior green candle")

    # Harami
    if _is_red(prev) and _is_green(last) and last["open"] > prev["close"] and last["close"] < prev["open"]:
        add("Bullish Harami", "bullish", "Inside candle bullish reversal")

    if _is_green(prev) and _is_red(last) and last["open"] < prev["close"] and last["close"] > prev["open"]:
        add("Bearish Harami", "bearish", "Inside candle bearish reversal")

    return patterns


def detect_chart_patterns(df: pd.DataFrame, lookback: int = 60) -> List[Dict]:
    """Detect classical chart formations over the lookback window."""
    patterns = []
    if len(df) < lookback:
        return patterns

    window = df.tail(lookback)
    highs = window["high"].values
    lows = window["low"].values
    closes = window["close"].values
    n = len(closes)

    # Find local extrema
    def local_maxima(arr, order=5):
        peaks = []
        for i in range(order, len(arr) - order):
            if arr[i] == max(arr[i - order: i + order + 1]):
                peaks.append((i, arr[i]))
        return peaks

    def local_minima(arr, order=5):
        troughs = []
        for i in range(order, len(arr) - order):
            if arr[i] == min(arr[i - order: i + order + 1]):
                troughs.append((i, arr[i]))
        return troughs

    peaks = local_maxima(highs)
    troughs = local_minima(lows)

    # Head and Shoulders
    if len(peaks) >= 3:
        for i in range(len(peaks) - 2):
            lp, lv = peaks[i]
            hp, hv = peaks[i + 1]
            rp, rv = peaks[i + 2]
            if hv > lv and hv > rv and abs(lv - rv) / hv < 0.05:
                patterns.append({
                    "name": "Head and Shoulders",
                    "direction": "bearish",
                    "description": "Classic reversal top — head is higher than both shoulders",
                    "confidence": 0.75,
                })
                break

    # Inverse H&S
    if len(troughs) >= 3:
        for i in range(len(troughs) - 2):
            lt, lv = troughs[i]
            ht, hv = troughs[i + 1]
            rt, rv = troughs[i + 2]
            if hv < lv and hv < rv and abs(lv - rv) / abs(hv) < 0.05:
                patterns.append({
                    "name": "Inverse Head and Shoulders",
                    "direction": "bullish",
                    "description": "Classic reversal bottom — head is lower than both shoulders",
                    "confidence": 0.75,
                })
                break

    # Double Top
    if len(peaks) >= 2:
        p1i, p1v = peaks[-2]
        p2i, p2v = peaks[-1]
        if abs(p1v - p2v) / p1v < 0.03 and p2i - p1i > 5:
            patterns.append({
                "name": "Double Top",
                "direction": "bearish",
                "description": "Price failed to break resistance twice — bearish reversal",
                "confidence": 0.70,
            })

    # Double Bottom
    if len(troughs) >= 2:
        t1i, t1v = troughs[-2]
        t2i, t2v = troughs[-1]
        if abs(t1v - t2v) / t1v < 0.03 and t2i - t1i > 5:
            patterns.append({
                "name": "Double Bottom",
                "direction": "bullish",
                "description": "Price found support twice — bullish reversal",
                "confidence": 0.70,
            })

    # Ascending Triangle
    if len(peaks) >= 2 and len(troughs) >= 2:
        recent_highs = [v for _, v in peaks[-3:]]
        recent_lows = [v for _, v in troughs[-3:]]
        if len(recent_highs) >= 2 and max(recent_highs) - min(recent_highs) < 0.02 * np.mean(recent_highs):
            if len(recent_lows) >= 2 and recent_lows[-1] > recent_lows[0]:
                patterns.append({
                    "name": "Ascending Triangle",
                    "direction": "bullish",
                    "description": "Flat resistance with rising support — bullish breakout likely",
                    "confidence": 0.65,
                })

    # Descending Triangle
    if len(peaks) >= 2 and len(troughs) >= 2:
        recent_highs = [v for _, v in peaks[-3:]]
        recent_lows = [v for _, v in troughs[-3:]]
        if len(recent_lows) >= 2 and max(recent_lows) - min(recent_lows) < 0.02 * np.mean(recent_lows):
            if len(recent_highs) >= 2 and recent_highs[-1] < recent_highs[0]:
                patterns.append({
                    "name": "Descending Triangle",
                    "direction": "bearish",
                    "description": "Flat support with falling resistance — bearish breakout likely",
                    "confidence": 0.65,
                })

    # Symmetrical Triangle (converging)
    if len(peaks) >= 2 and len(troughs) >= 2:
        recent_highs = [v for _, v in peaks[-3:]]
        recent_lows = [v for _, v in troughs[-3:]]
        if (len(recent_highs) >= 2 and recent_highs[-1] < recent_highs[0] and
                len(recent_lows) >= 2 and recent_lows[-1] > recent_lows[0]):
            patterns.append({
                "name": "Symmetrical Triangle",
                "direction": "neutral",
                "description": "Converging price action — breakout direction TBD",
                "confidence": 0.55,
            })

    # Cup and Handle (simplified)
    if n > 40:
        first_quarter = closes[:n // 4]
        middle = closes[n // 4: 3 * n // 4]
        last_quarter = closes[3 * n // 4:]
        if (np.mean(first_quarter) > np.mean(middle) and
                np.mean(last_quarter) > np.mean(middle) and
                abs(np.mean(first_quarter) - np.mean(last_quarter)) / np.mean(first_quarter) < 0.05):
            patterns.append({
                "name": "Cup and Handle",
                "direction": "bullish",
                "description": "U-shaped consolidation followed by handle — bullish continuation",
                "confidence": 0.60,
            })

    # Flag / Pennant (recent strong move then consolidation)
    if n > 20:
        prior = closes[:n - 10]
        flag = closes[n - 10:]
        prior_change = (prior[-1] - prior[0]) / prior[0]
        flag_range = (max(flag) - min(flag)) / np.mean(flag)

        if prior_change > 0.10 and flag_range < 0.04:
            patterns.append({
                "name": "Bull Flag",
                "direction": "bullish",
                "description": "Strong move up followed by tight consolidation — continuation pattern",
                "confidence": 0.65,
            })
        elif prior_change < -0.10 and flag_range < 0.04:
            patterns.append({
                "name": "Bear Flag",
                "direction": "bearish",
                "description": "Strong move down followed by tight consolidation — continuation pattern",
                "confidence": 0.65,
            })

    return patterns


def detect_divergences(df: pd.DataFrame, rsi_series: pd.Series, lookback: int = 30) -> List[Dict]:
    """Detect RSI divergences (bullish/bearish)."""
    divergences = []
    if len(df) < lookback:
        return divergences

    prices = df["close"].tail(lookback).values
    rsi_vals = rsi_series.tail(lookback).values

    def find_lows(arr, order=3):
        lows = []
        for i in range(order, len(arr) - order):
            if arr[i] <= min(arr[i - order: i + order + 1]):
                lows.append((i, arr[i]))
        return lows

    def find_highs(arr, order=3):
        highs = []
        for i in range(order, len(arr) - order):
            if arr[i] >= max(arr[i - order: i + order + 1]):
                highs.append((i, arr[i]))
        return highs

    price_lows = find_lows(prices)
    rsi_lows = find_lows(rsi_vals)

    # Bullish divergence: price makes lower low, RSI makes higher low
    if len(price_lows) >= 2 and len(rsi_lows) >= 2:
        pl1, pv1 = price_lows[-2]
        pl2, pv2 = price_lows[-1]
        rl1, rv1 = rsi_lows[-2]
        rl2, rv2 = rsi_lows[-1]
        if pv2 < pv1 and rv2 > rv1 and abs(pl2 - rl2) < 3:
            divergences.append({
                "type": "Bullish Divergence",
                "direction": "bullish",
                "description": "Price made lower low but RSI made higher low — potential reversal up",
            })

    price_highs = find_highs(prices)
    rsi_highs = find_highs(rsi_vals)

    # Bearish divergence: price makes higher high, RSI makes lower high
    if len(price_highs) >= 2 and len(rsi_highs) >= 2:
        ph1, pv1 = price_highs[-2]
        ph2, pv2 = price_highs[-1]
        rh1, rv1 = rsi_highs[-2]
        rh2, rv2 = rsi_highs[-1]
        if pv2 > pv1 and rv2 < rv1 and abs(ph2 - rh2) < 3:
            divergences.append({
                "type": "Bearish Divergence",
                "direction": "bearish",
                "description": "Price made higher high but RSI made lower high — potential reversal down",
            })

    return divergences


def market_regime(df: pd.DataFrame) -> Dict:
    """Classify market regime: Trending Up / Down / Sideways / Volatile."""
    if len(df) < 50:
        return {"regime": "Unknown", "confidence": 0}

    closes = df["close"].tail(50).values
    sma20 = np.mean(closes[-20:])
    sma50 = np.mean(closes)
    returns = np.diff(closes) / closes[:-1]
    volatility = np.std(returns) * np.sqrt(252)
    trend_slope = np.polyfit(range(len(closes)), closes, 1)[0]
    trend_strength = abs(trend_slope) / np.mean(closes) * 252

    if volatility > 0.40:
        regime = "High Volatility"
    elif trend_strength > 0.20 and sma20 > sma50:
        regime = "Trending Up"
    elif trend_strength > 0.20 and sma20 < sma50:
        regime = "Trending Down"
    elif trend_strength < 0.05:
        regime = "Sideways / Ranging"
    else:
        regime = "Mild Trend"

    r_squared = np.corrcoef(range(len(closes)), closes)[0, 1] ** 2

    return {
        "regime": regime,
        "volatility_annualized": volatility * 100,
        "trend_slope": trend_slope,
        "r_squared": r_squared,
        "confidence": r_squared * 100,
    }
