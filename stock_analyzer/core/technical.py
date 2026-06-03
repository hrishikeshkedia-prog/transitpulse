"""
Comprehensive technical analysis module with 50+ indicators.
All indicators are computed from scratch using pandas/numpy.
"""
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from config import (
    RSI_PERIOD, MACD_FAST, MACD_SLOW, MACD_SIGNAL,
    BB_PERIOD, BB_STD, ATR_PERIOD, ADX_PERIOD,
    STOCH_K, STOCH_D, CCI_PERIOD, WILLIAMS_PERIOD, MFI_PERIOD, CMF_PERIOD,
    FIBONACCI_LEVELS,
)


def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()


def _rma(series: pd.Series, period: int) -> pd.Series:
    """Wilder's Moving Average (used in RSI, ATR)."""
    return series.ewm(alpha=1 / period, adjust=False).mean()


# ─── Trend Indicators ────────────────────────────────────────────────────────

def sma(df: pd.DataFrame, period: int) -> pd.Series:
    return _sma(df["close"], period)


def ema(df: pd.DataFrame, period: int) -> pd.Series:
    return _ema(df["close"], period)


def wma(df: pd.DataFrame, period: int) -> pd.Series:
    weights = np.arange(1, period + 1)
    return df["close"].rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)


def hma(df: pd.DataFrame, period: int) -> pd.Series:
    """Hull Moving Average."""
    half = int(period / 2)
    sqrt = int(np.sqrt(period))
    wma1 = wma(df.assign(close=df["close"]), half)
    wma2 = wma(df.assign(close=df["close"]), period)
    raw = 2 * wma1 - wma2
    tmp = df.copy()
    tmp["close"] = raw
    return wma(tmp, sqrt)


def dema(df: pd.DataFrame, period: int) -> pd.Series:
    """Double Exponential Moving Average."""
    e = _ema(df["close"], period)
    return 2 * e - _ema(e, period)


def tema(df: pd.DataFrame, period: int) -> pd.Series:
    """Triple Exponential Moving Average."""
    e1 = _ema(df["close"], period)
    e2 = _ema(e1, period)
    e3 = _ema(e2, period)
    return 3 * e1 - 3 * e2 + e3


def vwap(df: pd.DataFrame) -> pd.Series:
    """Volume Weighted Average Price (intraday style on daily reset)."""
    typical = (df["high"] + df["low"] + df["close"]) / 3
    cum_vol = df["volume"].cumsum()
    cum_tpv = (typical * df["volume"]).cumsum()
    return cum_tpv / cum_vol


def ichimoku(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """Ichimoku Cloud components."""
    h9 = df["high"].rolling(9).max()
    l9 = df["low"].rolling(9).min()
    tenkan = (h9 + l9) / 2

    h26 = df["high"].rolling(26).max()
    l26 = df["low"].rolling(26).min()
    kijun = (h26 + l26) / 2

    senkou_a = ((tenkan + kijun) / 2).shift(26)

    h52 = df["high"].rolling(52).max()
    l52 = df["low"].rolling(52).min()
    senkou_b = ((h52 + l52) / 2).shift(26)

    chikou = df["close"].shift(-26)

    return {
        "tenkan": tenkan,
        "kijun": kijun,
        "senkou_a": senkou_a,
        "senkou_b": senkou_b,
        "chikou": chikou,
    }


def parabolic_sar(df: pd.DataFrame, step: float = 0.02, max_step: float = 0.2) -> pd.Series:
    """Parabolic SAR."""
    high = df["high"].values
    low = df["low"].values
    close = df["close"].values
    n = len(close)
    sar = np.zeros(n)
    ep = np.zeros(n)
    af = np.zeros(n)
    bull = True

    sar[0] = low[0]
    ep[0] = high[0]
    af[0] = step

    for i in range(1, n):
        if bull:
            sar[i] = sar[i - 1] + af[i - 1] * (ep[i - 1] - sar[i - 1])
            sar[i] = min(sar[i], low[i - 1], low[i - 2] if i > 1 else low[i - 1])
            if low[i] < sar[i]:
                bull = False
                sar[i] = ep[i - 1]
                ep[i] = low[i]
                af[i] = step
            else:
                ep[i] = max(ep[i - 1], high[i])
                af[i] = min(af[i - 1] + step if high[i] > ep[i - 1] else af[i - 1], max_step)
        else:
            sar[i] = sar[i - 1] + af[i - 1] * (ep[i - 1] - sar[i - 1])
            sar[i] = max(sar[i], high[i - 1], high[i - 2] if i > 1 else high[i - 1])
            if high[i] > sar[i]:
                bull = True
                sar[i] = ep[i - 1]
                ep[i] = high[i]
                af[i] = step
            else:
                ep[i] = min(ep[i - 1], low[i])
                af[i] = min(af[i - 1] + step if low[i] < ep[i - 1] else af[i - 1], max_step)

    return pd.Series(sar, index=df.index)


def supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> Dict[str, pd.Series]:
    """Supertrend indicator."""
    atr_val = atr(df, period)
    hl2 = (df["high"] + df["low"]) / 2
    upper_band = hl2 + multiplier * atr_val
    lower_band = hl2 - multiplier * atr_val

    supertrend_vals = pd.Series(np.nan, index=df.index)
    direction = pd.Series(1, index=df.index)

    for i in range(1, len(df)):
        upper_band.iloc[i] = min(upper_band.iloc[i], upper_band.iloc[i - 1]) if df["close"].iloc[i - 1] <= upper_band.iloc[i - 1] else upper_band.iloc[i]
        lower_band.iloc[i] = max(lower_band.iloc[i], lower_band.iloc[i - 1]) if df["close"].iloc[i - 1] >= lower_band.iloc[i - 1] else lower_band.iloc[i]

        if supertrend_vals.iloc[i - 1] == upper_band.iloc[i - 1]:
            direction.iloc[i] = -1 if df["close"].iloc[i] > upper_band.iloc[i] else 1
        else:
            direction.iloc[i] = 1 if df["close"].iloc[i] < lower_band.iloc[i] else -1

        supertrend_vals.iloc[i] = lower_band.iloc[i] if direction.iloc[i] == -1 else upper_band.iloc[i]

    return {"supertrend": supertrend_vals, "direction": direction}


# ─── Momentum Indicators ─────────────────────────────────────────────────────

def rsi(df: pd.DataFrame, period: int = RSI_PERIOD) -> pd.Series:
    """Relative Strength Index."""
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = _rma(gain, period)
    avg_loss = _rma(loss, period)
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(
    df: pd.DataFrame,
    fast: int = MACD_FAST,
    slow: int = MACD_SLOW,
    signal: int = MACD_SIGNAL,
) -> Dict[str, pd.Series]:
    """MACD, Signal, and Histogram."""
    fast_ema = _ema(df["close"], fast)
    slow_ema = _ema(df["close"], slow)
    macd_line = fast_ema - slow_ema
    signal_line = _ema(macd_line, signal)
    histogram = macd_line - signal_line
    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


def stochastic(
    df: pd.DataFrame, k_period: int = STOCH_K, d_period: int = STOCH_D
) -> Dict[str, pd.Series]:
    """Stochastic Oscillator %K and %D."""
    lowest_low = df["low"].rolling(k_period).min()
    highest_high = df["high"].rolling(k_period).max()
    k = 100 * (df["close"] - lowest_low) / (highest_high - lowest_low).replace(0, np.nan)
    d = _sma(k, d_period)
    return {"k": k, "d": d}


def cci(df: pd.DataFrame, period: int = CCI_PERIOD) -> pd.Series:
    """Commodity Channel Index."""
    typical = (df["high"] + df["low"] + df["close"]) / 3
    mean = typical.rolling(period).mean()
    mad = typical.rolling(period).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
    return (typical - mean) / (0.015 * mad.replace(0, np.nan))


def williams_r(df: pd.DataFrame, period: int = WILLIAMS_PERIOD) -> pd.Series:
    """Williams %R."""
    highest_high = df["high"].rolling(period).max()
    lowest_low = df["low"].rolling(period).min()
    return -100 * (highest_high - df["close"]) / (highest_high - lowest_low).replace(0, np.nan)


def roc(df: pd.DataFrame, period: int = 12) -> pd.Series:
    """Rate of Change."""
    return (df["close"] - df["close"].shift(period)) / df["close"].shift(period) * 100


def mom(df: pd.DataFrame, period: int = 10) -> pd.Series:
    """Momentum."""
    return df["close"] - df["close"].shift(period)


def tsi(df: pd.DataFrame, long: int = 25, short: int = 13) -> pd.Series:
    """True Strength Index."""
    diff = df["close"].diff()
    abs_diff = diff.abs()
    double_smoothed = _ema(_ema(diff, long), short)
    double_smoothed_abs = _ema(_ema(abs_diff, long), short)
    return 100 * double_smoothed / double_smoothed_abs.replace(0, np.nan)


def ultimate_oscillator(df: pd.DataFrame) -> pd.Series:
    """Ultimate Oscillator."""
    prev_close = df["close"].shift(1)
    bp = df["close"] - pd.concat([df["low"], prev_close], axis=1).min(axis=1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)

    avg7 = bp.rolling(7).sum() / tr.rolling(7).sum()
    avg14 = bp.rolling(14).sum() / tr.rolling(14).sum()
    avg28 = bp.rolling(28).sum() / tr.rolling(28).sum()
    return 100 * (4 * avg7 + 2 * avg14 + avg28) / 7


def awesome_oscillator(df: pd.DataFrame) -> pd.Series:
    """Awesome Oscillator."""
    midpoint = (df["high"] + df["low"]) / 2
    return _sma(midpoint, 5) - _sma(midpoint, 34)


# ─── Volatility Indicators ───────────────────────────────────────────────────

def atr(df: pd.DataFrame, period: int = ATR_PERIOD) -> pd.Series:
    """Average True Range."""
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return _rma(tr, period)


def bollinger_bands(
    df: pd.DataFrame, period: int = BB_PERIOD, num_std: float = BB_STD
) -> Dict[str, pd.Series]:
    """Bollinger Bands."""
    mid = _sma(df["close"], period)
    std = df["close"].rolling(period).std()
    upper = mid + num_std * std
    lower = mid - num_std * std
    width = (upper - lower) / mid
    pct_b = (df["close"] - lower) / (upper - lower).replace(0, np.nan)
    return {"upper": upper, "middle": mid, "lower": lower, "width": width, "pct_b": pct_b}


def keltner_channel(
    df: pd.DataFrame, ema_period: int = 20, atr_period: int = 10, multiplier: float = 2.0
) -> Dict[str, pd.Series]:
    """Keltner Channel."""
    mid = _ema(df["close"], ema_period)
    a = atr(df, atr_period)
    return {"upper": mid + multiplier * a, "middle": mid, "lower": mid - multiplier * a}


def donchian_channel(df: pd.DataFrame, period: int = 20) -> Dict[str, pd.Series]:
    """Donchian Channel."""
    upper = df["high"].rolling(period).max()
    lower = df["low"].rolling(period).min()
    mid = (upper + lower) / 2
    return {"upper": upper, "middle": mid, "lower": lower}


def historical_volatility(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Annualized Historical Volatility."""
    log_returns = np.log(df["close"] / df["close"].shift(1))
    return log_returns.rolling(period).std() * np.sqrt(252) * 100


def chaikin_volatility(df: pd.DataFrame, ema_period: int = 10, roc_period: int = 10) -> pd.Series:
    """Chaikin Volatility."""
    hl_diff = df["high"] - df["low"]
    return roc(pd.DataFrame({"close": _ema(hl_diff, ema_period)}), roc_period)


# ─── Volume Indicators ───────────────────────────────────────────────────────

def obv(df: pd.DataFrame) -> pd.Series:
    """On-Balance Volume."""
    direction = np.sign(df["close"].diff()).fillna(0)
    return (direction * df["volume"]).cumsum()


def mfi(df: pd.DataFrame, period: int = MFI_PERIOD) -> pd.Series:
    """Money Flow Index."""
    typical = (df["high"] + df["low"] + df["close"]) / 3
    raw_money_flow = typical * df["volume"]
    pos_flow = raw_money_flow.where(typical > typical.shift(1), 0)
    neg_flow = raw_money_flow.where(typical < typical.shift(1), 0)
    pos_sum = pos_flow.rolling(period).sum()
    neg_sum = neg_flow.rolling(period).sum()
    mfr = pos_sum / neg_sum.replace(0, np.nan)
    return 100 - (100 / (1 + mfr))


def cmf(df: pd.DataFrame, period: int = CMF_PERIOD) -> pd.Series:
    """Chaikin Money Flow."""
    clv = ((df["close"] - df["low"]) - (df["high"] - df["close"])) / (df["high"] - df["low"]).replace(0, np.nan)
    mfv = clv * df["volume"]
    return mfv.rolling(period).sum() / df["volume"].rolling(period).sum()


def force_index(df: pd.DataFrame, period: int = 13) -> pd.Series:
    """Force Index."""
    raw = df["close"].diff() * df["volume"]
    return _ema(raw, period)


def ease_of_movement(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Ease of Movement."""
    dm = ((df["high"] + df["low"]) / 2) - ((df["high"].shift(1) + df["low"].shift(1)) / 2)
    br = df["volume"] / (df["high"] - df["low"]).replace(0, np.nan)
    eom = dm / br
    return _sma(eom, period)


def volume_sma(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Volume Simple Moving Average."""
    return _sma(df["volume"], period)


def vpt(df: pd.DataFrame) -> pd.Series:
    """Volume Price Trend."""
    return (df["volume"] * df["close"].pct_change()).cumsum()


# ─── Trend Strength ──────────────────────────────────────────────────────────

def adx(df: pd.DataFrame, period: int = ADX_PERIOD) -> Dict[str, pd.Series]:
    """Average Directional Index (+DI, -DI, ADX)."""
    high_diff = df["high"].diff()
    low_diff = df["low"].diff()

    plus_dm = high_diff.where((high_diff > low_diff.abs()) & (high_diff > 0), 0.0)
    minus_dm = (-low_diff).where((low_diff.abs() > high_diff) & (low_diff < 0), 0.0)

    tr_val = atr(df, 1)  # True Range (not smoothed)
    prev_close = df["close"].shift(1)
    tr_raw = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)

    atr_smooth = _rma(tr_raw, period)
    plus_di = 100 * _rma(plus_dm, period) / atr_smooth.replace(0, np.nan)
    minus_di = 100 * _rma(minus_dm, period) / atr_smooth.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx_line = _rma(dx, period)

    return {"adx": adx_line, "plus_di": plus_di, "minus_di": minus_di}


def aroon(df: pd.DataFrame, period: int = 25) -> Dict[str, pd.Series]:
    """Aroon Oscillator."""
    up = df["high"].rolling(period + 1).apply(lambda x: x.argmax(), raw=True)
    down = df["low"].rolling(period + 1).apply(lambda x: x.argmin(), raw=True)
    aroon_up = (period - (period - up)) / period * 100
    aroon_down = (period - (period - down)) / period * 100
    return {"aroon_up": aroon_up, "aroon_down": aroon_down, "oscillator": aroon_up - aroon_down}


def vortex(df: pd.DataFrame, period: int = 14) -> Dict[str, pd.Series]:
    """Vortex Indicator."""
    vm_plus = (df["high"] - df["low"].shift(1)).abs()
    vm_minus = (df["low"] - df["high"].shift(1)).abs()

    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)

    vi_plus = vm_plus.rolling(period).sum() / tr.rolling(period).sum()
    vi_minus = vm_minus.rolling(period).sum() / tr.rolling(period).sum()
    return {"vi_plus": vi_plus, "vi_minus": vi_minus}


def dpo(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Detrended Price Oscillator."""
    shift = period // 2 + 1
    return df["close"] - _sma(df["close"], period).shift(shift)


def mass_index(df: pd.DataFrame, fast: int = 9, slow: int = 25) -> pd.Series:
    """Mass Index."""
    hl_range = df["high"] - df["low"]
    ema1 = _ema(hl_range, fast)
    ema2 = _ema(ema1, fast)
    ratio = ema1 / ema2.replace(0, np.nan)
    return ratio.rolling(slow).sum()


# ─── Support / Resistance / Fibonacci ───────────────────────────────────────

def pivot_points(df: pd.DataFrame) -> Dict[str, float]:
    """Classic Pivot Points from last completed candle."""
    last = df.iloc[-1]
    pivot = (last["high"] + last["low"] + last["close"]) / 3
    r1 = 2 * pivot - last["low"]
    s1 = 2 * pivot - last["high"]
    r2 = pivot + (last["high"] - last["low"])
    s2 = pivot - (last["high"] - last["low"])
    r3 = last["high"] + 2 * (pivot - last["low"])
    s3 = last["low"] - 2 * (last["high"] - pivot)
    return {"P": pivot, "R1": r1, "R2": r2, "R3": r3, "S1": s1, "S2": s2, "S3": s3}


def fibonacci_retracements(df: pd.DataFrame, lookback: int = 90) -> Dict[str, float]:
    """Fibonacci retracement levels from the swing high/low in the lookback window."""
    window = df.tail(lookback)
    high = window["high"].max()
    low = window["low"].min()
    diff = high - low
    levels = {}
    for level in FIBONACCI_LEVELS:
        price = high - level * diff
        levels[f"{level:.3f}"] = price
    return levels


def support_resistance_levels(df: pd.DataFrame, lookback: int = 50, prominence: float = 0.02) -> Dict[str, list]:
    """Detect support and resistance levels using local extrema."""
    window = df.tail(lookback)
    closes = window["close"].values

    supports = []
    resistances = []

    for i in range(2, len(closes) - 2):
        if closes[i] < closes[i - 1] and closes[i] < closes[i - 2] and closes[i] < closes[i + 1] and closes[i] < closes[i + 2]:
            supports.append(float(closes[i]))
        if closes[i] > closes[i - 1] and closes[i] > closes[i - 2] and closes[i] > closes[i + 1] and closes[i] > closes[i + 2]:
            resistances.append(float(closes[i]))

    current = closes[-1]
    supports = sorted([s for s in supports if s < current], reverse=True)[:5]
    resistances = sorted([r for r in resistances if r > current])[:5]

    return {"support": supports, "resistance": resistances}


# ─── Statistical Metrics ─────────────────────────────────────────────────────

def zscore(series: pd.Series, period: int = 20) -> pd.Series:
    """Z-score of a series over a rolling window."""
    mean = series.rolling(period).mean()
    std = series.rolling(period).std()
    return (series - mean) / std.replace(0, np.nan)


def linear_regression_channel(df: pd.DataFrame, period: int = 20) -> Dict[str, pd.Series]:
    """Linear regression line and channel."""
    n = len(df)
    lr = pd.Series(np.nan, index=df.index)
    upper = pd.Series(np.nan, index=df.index)
    lower = pd.Series(np.nan, index=df.index)

    for i in range(period - 1, n):
        x = np.arange(period)
        y = df["close"].iloc[i - period + 1: i + 1].values
        coeffs = np.polyfit(x, y, 1)
        lr.iloc[i] = np.polyval(coeffs, period - 1)
        residuals = y - np.polyval(coeffs, x)
        std_dev = np.std(residuals)
        upper.iloc[i] = lr.iloc[i] + 2 * std_dev
        lower.iloc[i] = lr.iloc[i] - 2 * std_dev

    return {"lr": lr, "upper": upper, "lower": lower}


# ─── Master Compute Function ─────────────────────────────────────────────────

def compute_all(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """Compute all technical indicators and return as a dict of Series."""
    result = {}

    # Moving Averages
    for period in [9, 20, 50, 100, 200]:
        result[f"sma_{period}"] = sma(df, period)
        result[f"ema_{period}"] = ema(df, period)

    result["hma_20"] = hma(df, 20)
    result["dema_20"] = dema(df, 20)
    result["tema_20"] = tema(df, 20)
    result["vwap"] = vwap(df)
    result["psar"] = parabolic_sar(df)

    # Ichimoku
    ich = ichimoku(df)
    result.update({f"ich_{k}": v for k, v in ich.items()})

    # Momentum
    result["rsi_14"] = rsi(df, 14)
    result["rsi_7"] = rsi(df, 7)
    result["rsi_21"] = rsi(df, 21)

    macd_data = macd(df)
    result["macd"] = macd_data["macd"]
    result["macd_signal"] = macd_data["signal"]
    result["macd_hist"] = macd_data["histogram"]

    stoch = stochastic(df)
    result["stoch_k"] = stoch["k"]
    result["stoch_d"] = stoch["d"]

    result["cci_20"] = cci(df, 20)
    result["williams_r"] = williams_r(df)
    result["roc_12"] = roc(df, 12)
    result["roc_6"] = roc(df, 6)
    result["mom_10"] = mom(df, 10)
    result["tsi"] = tsi(df)
    result["uo"] = ultimate_oscillator(df)
    result["ao"] = awesome_oscillator(df)

    # Volatility
    result["atr_14"] = atr(df, 14)
    result["atr_7"] = atr(df, 7)

    bb = bollinger_bands(df)
    result["bb_upper"] = bb["upper"]
    result["bb_middle"] = bb["middle"]
    result["bb_lower"] = bb["lower"]
    result["bb_width"] = bb["width"]
    result["bb_pct_b"] = bb["pct_b"]

    kc = keltner_channel(df)
    result["kc_upper"] = kc["upper"]
    result["kc_middle"] = kc["middle"]
    result["kc_lower"] = kc["lower"]

    dc = donchian_channel(df)
    result["dc_upper"] = dc["upper"]
    result["dc_middle"] = dc["middle"]
    result["dc_lower"] = dc["lower"]

    result["hv_20"] = historical_volatility(df, 20)
    result["hv_10"] = historical_volatility(df, 10)

    # Volume
    result["obv"] = obv(df)
    result["mfi_14"] = mfi(df, 14)
    result["cmf_20"] = cmf(df, 20)
    result["force_index"] = force_index(df)
    result["eom"] = ease_of_movement(df)
    result["vol_sma_20"] = volume_sma(df, 20)
    result["vpt"] = vpt(df)

    # Trend Strength
    adx_data = adx(df)
    result["adx"] = adx_data["adx"]
    result["plus_di"] = adx_data["plus_di"]
    result["minus_di"] = adx_data["minus_di"]

    aroon_data = aroon(df)
    result["aroon_up"] = aroon_data["aroon_up"]
    result["aroon_down"] = aroon_data["aroon_down"]
    result["aroon_osc"] = aroon_data["oscillator"]

    vortex_data = vortex(df)
    result["vi_plus"] = vortex_data["vi_plus"]
    result["vi_minus"] = vortex_data["vi_minus"]

    result["dpo_20"] = dpo(df, 20)
    result["mass_index"] = mass_index(df)

    # Supertrend
    st = supertrend(df)
    result["supertrend"] = st["supertrend"]
    result["supertrend_dir"] = st["direction"]

    # LR Channel
    lr = linear_regression_channel(df)
    result["lr_line"] = lr["lr"]
    result["lr_upper"] = lr["upper"]
    result["lr_lower"] = lr["lower"]

    # Returns
    result["returns"] = df["close"].pct_change()
    result["log_returns"] = np.log(df["close"] / df["close"].shift(1))
    result["vol_ratio"] = df["volume"] / result["vol_sma_20"]
    result["zscore_20"] = zscore(df["close"], 20)

    return result


def generate_signals(df: pd.DataFrame, indicators: Dict[str, pd.Series]) -> Dict[str, any]:
    """
    Generate a composite buy/sell/hold signal from all indicators.
    Returns a dict with individual signals and a composite score [-1, 1].
    """
    signals = {}
    scores = []

    last = len(df) - 1
    close = df["close"].iloc[last]

    # — Trend signals —
    for period in [20, 50, 200]:
        sma_key = f"sma_{period}"
        if sma_key in indicators and not pd.isna(indicators[sma_key].iloc[last]):
            score = 1 if close > indicators[sma_key].iloc[last] else -1
            signals[f"price_vs_sma{period}"] = score
            scores.append(("trend", score))

    # Golden/Death Cross
    if "sma_50" in indicators and "sma_200" in indicators:
        sma50 = indicators["sma_50"].iloc[last]
        sma200 = indicators["sma_200"].iloc[last]
        prev_sma50 = indicators["sma_50"].iloc[last - 1] if last > 0 else sma50
        prev_sma200 = indicators["sma_200"].iloc[last - 1] if last > 0 else sma200
        if not any(pd.isna([sma50, sma200, prev_sma50, prev_sma200])):
            if prev_sma50 <= prev_sma200 and sma50 > sma200:
                signals["golden_cross"] = 1
                scores.append(("trend", 1))
            elif prev_sma50 >= prev_sma200 and sma50 < sma200:
                signals["death_cross"] = -1
                scores.append(("trend", -1))

    # Supertrend
    if "supertrend_dir" in indicators:
        st_dir = indicators["supertrend_dir"].iloc[last]
        signals["supertrend"] = int(-st_dir)
        scores.append(("trend", int(-st_dir)))

    # Ichimoku
    if "ich_tenkan" in indicators and "ich_kijun" in indicators:
        tenkan = indicators["ich_tenkan"].iloc[last]
        kijun = indicators["ich_kijun"].iloc[last]
        if not any(pd.isna([tenkan, kijun])):
            score = 1 if tenkan > kijun else -1
            signals["ichimoku_tk"] = score
            scores.append(("trend", score))

    # — Momentum signals —
    # RSI
    if "rsi_14" in indicators:
        rsi_val = indicators["rsi_14"].iloc[last]
        if not pd.isna(rsi_val):
            if rsi_val < 30:
                signals["rsi"] = 1
                scores.append(("momentum", 1))
            elif rsi_val > 70:
                signals["rsi"] = -1
                scores.append(("momentum", -1))
            else:
                signals["rsi"] = 0
                scores.append(("momentum", 0))

    # MACD
    if "macd_hist" in indicators:
        hist = indicators["macd_hist"].iloc[last]
        prev_hist = indicators["macd_hist"].iloc[last - 1] if last > 0 else hist
        if not any(pd.isna([hist, prev_hist])):
            if prev_hist <= 0 and hist > 0:
                signals["macd_cross"] = 1
                scores.append(("momentum", 1))
            elif prev_hist >= 0 and hist < 0:
                signals["macd_cross"] = -1
                scores.append(("momentum", -1))
            else:
                signals["macd_trend"] = 1 if hist > 0 else -1
                scores.append(("momentum", 0.5 if hist > 0 else -0.5))

    # Stochastic
    if "stoch_k" in indicators and "stoch_d" in indicators:
        k_val = indicators["stoch_k"].iloc[last]
        d_val = indicators["stoch_d"].iloc[last]
        if not any(pd.isna([k_val, d_val])):
            if k_val < 20 and d_val < 20:
                signals["stochastic"] = 1
                scores.append(("momentum", 1))
            elif k_val > 80 and d_val > 80:
                signals["stochastic"] = -1
                scores.append(("momentum", -1))
            else:
                signals["stochastic"] = 0
                scores.append(("momentum", 0))

    # CCI
    if "cci_20" in indicators:
        cci_val = indicators["cci_20"].iloc[last]
        if not pd.isna(cci_val):
            if cci_val < -100:
                signals["cci"] = 1
                scores.append(("momentum", 1))
            elif cci_val > 100:
                signals["cci"] = -1
                scores.append(("momentum", -1))
            else:
                scores.append(("momentum", 0))

    # ADX trend strength
    if "adx" in indicators:
        adx_val = indicators["adx"].iloc[last]
        plus_di_val = indicators["plus_di"].iloc[last] if "plus_di" in indicators else None
        minus_di_val = indicators["minus_di"].iloc[last] if "minus_di" in indicators else None
        if not any(pd.isna([adx_val, plus_di_val, minus_di_val])):
            if adx_val > 25:
                score = 1 if plus_di_val > minus_di_val else -1
                signals["adx"] = score
                scores.append(("trend", score))

    # — Volume signals —
    if "cmf_20" in indicators:
        cmf_val = indicators["cmf_20"].iloc[last]
        if not pd.isna(cmf_val):
            score = 1 if cmf_val > 0 else -1
            signals["cmf"] = score
            scores.append(("volume", score))

    if "mfi_14" in indicators:
        mfi_val = indicators["mfi_14"].iloc[last]
        if not pd.isna(mfi_val):
            if mfi_val < 20:
                signals["mfi"] = 1
                scores.append(("volume", 1))
            elif mfi_val > 80:
                signals["mfi"] = -1
                scores.append(("volume", -1))
            else:
                scores.append(("volume", 0))

    # Volume breakout
    if "vol_ratio" in indicators:
        vr = indicators["vol_ratio"].iloc[last]
        if not pd.isna(vr) and vr > 2.0:
            trend_scores = [s for cat, s in scores if cat == "trend"]
            direction = 1 if trend_scores and np.mean(trend_scores) > 0 else -1
            signals["volume_breakout"] = direction
            scores.append(("volume", direction))

    # — Volatility signals —
    if "bb_pct_b" in indicators:
        pct_b = indicators["bb_pct_b"].iloc[last]
        if not pd.isna(pct_b):
            if pct_b < 0:
                signals["bb_squeeze"] = 1
                scores.append(("volatility", 1))
            elif pct_b > 1:
                signals["bb_squeeze"] = -1
                scores.append(("volatility", -1))
            else:
                scores.append(("volatility", 0))

    # Compute weighted composite score
    weights = {"trend": 0.30, "momentum": 0.30, "volume": 0.20, "volatility": 0.20}
    category_scores = {}
    for cat in weights:
        cat_items = [s for c, s in scores if c == cat]
        category_scores[cat] = np.mean(cat_items) if cat_items else 0.0

    composite = sum(weights[cat] * category_scores[cat] for cat in weights)

    if composite > 0.3:
        recommendation = "STRONG BUY"
    elif composite > 0.1:
        recommendation = "BUY"
    elif composite < -0.3:
        recommendation = "STRONG SELL"
    elif composite < -0.1:
        recommendation = "SELL"
    else:
        recommendation = "HOLD"

    return {
        "individual": signals,
        "category_scores": category_scores,
        "composite": composite,
        "recommendation": recommendation,
    }
