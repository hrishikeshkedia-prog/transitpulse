"""
Portfolio analysis: correlation, risk/return metrics, drawdown, sector exposure.
"""
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from config import RISK_FREE_RATE, TRADING_DAYS


def build_returns_matrix(price_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build aligned daily returns matrix from dict of price DataFrames."""
    series = {}
    for sym, df in price_dict.items():
        if not df.empty:
            series[sym] = df["close"].pct_change()
    if not series:
        return pd.DataFrame()
    returns = pd.DataFrame(series).dropna(how="all")
    return returns


def correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    return returns.corr()


def portfolio_performance(
    returns: pd.DataFrame, weights: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """Calculate portfolio-level return, volatility, and Sharpe."""
    if weights is None:
        weights = np.ones(len(returns.columns)) / len(returns.columns)

    weights = np.array(weights)
    weights = weights / weights.sum()

    port_returns = (returns * weights).sum(axis=1).dropna()
    ann_return = port_returns.mean() * TRADING_DAYS * 100
    ann_vol = port_returns.std() * np.sqrt(TRADING_DAYS) * 100
    sharpe = (port_returns.mean() - RISK_FREE_RATE / TRADING_DAYS) / port_returns.std() * np.sqrt(TRADING_DAYS)

    # Max drawdown
    cumulative = (1 + port_returns).cumprod()
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    max_dd = drawdown.min() * 100

    # Sortino
    downside = port_returns[port_returns < 0]
    sortino = (port_returns.mean() - RISK_FREE_RATE / TRADING_DAYS) / (downside.std() or 1e-8) * np.sqrt(TRADING_DAYS)

    return {
        "annual_return": ann_return,
        "annual_volatility": ann_vol,
        "sharpe_ratio": float(sharpe),
        "sortino_ratio": float(sortino),
        "max_drawdown": float(max_dd),
        "weights": dict(zip(returns.columns, weights)),
    }


def individual_metrics(returns: pd.DataFrame) -> pd.DataFrame:
    """Per-asset metrics."""
    rows = []
    for col in returns.columns:
        r = returns[col].dropna()
        ann_ret = r.mean() * TRADING_DAYS * 100
        ann_vol = r.std() * np.sqrt(TRADING_DAYS) * 100
        sharpe = (r.mean() - RISK_FREE_RATE / TRADING_DAYS) / (r.std() or 1e-8) * np.sqrt(TRADING_DAYS)
        downside = r[r < 0]
        sortino = (r.mean() - RISK_FREE_RATE / TRADING_DAYS) / (downside.std() or 1e-8) * np.sqrt(TRADING_DAYS)
        cum = (1 + r).cumprod()
        peak = cum.cummax()
        max_dd = ((cum - peak) / peak).min() * 100
        skew = float(stats.skew(r))
        kurt = float(stats.kurtosis(r))
        rows.append({
            "symbol": col,
            "ann_return_%": round(ann_ret, 2),
            "ann_vol_%": round(ann_vol, 2),
            "sharpe": round(sharpe, 3),
            "sortino": round(sortino, 3),
            "max_drawdown_%": round(max_dd, 2),
            "skewness": round(skew, 3),
            "kurtosis": round(kurt, 3),
        })
    return pd.DataFrame(rows).set_index("symbol")


def portfolio_var(returns: pd.DataFrame, weights: np.ndarray, confidence: float = 0.95) -> float:
    """Portfolio Value at Risk."""
    port_returns = (returns * weights).sum(axis=1).dropna()
    return float(np.percentile(port_returns, (1 - confidence) * 100) * 100)


def contribution_to_risk(
    returns: pd.DataFrame, weights: np.ndarray
) -> pd.Series:
    """Marginal risk contribution of each asset."""
    cov = returns.cov().values * TRADING_DAYS
    port_var = weights @ cov @ weights
    if port_var == 0:
        return pd.Series(np.zeros(len(weights)), index=returns.columns)
    marginal = cov @ weights
    contribution = weights * marginal / port_var
    return pd.Series(contribution * 100, index=returns.columns)


def rolling_portfolio_sharpe(
    returns: pd.DataFrame, weights: np.ndarray, window: int = 60
) -> pd.Series:
    """Rolling portfolio Sharpe ratio."""
    port_returns = (returns * weights).sum(axis=1).dropna()
    return port_returns.rolling(window).apply(
        lambda x: (x.mean() / (x.std() or 1e-8)) * np.sqrt(TRADING_DAYS)
    )


def sector_allocation(symbols: List[str], weights: np.ndarray, info_dict: Dict) -> Dict[str, float]:
    """Compute sector allocation percentages."""
    allocations = {}
    for sym, w in zip(symbols, weights):
        info = info_dict.get(sym, {})
        sector = info.get("sector", "Unknown") or "Unknown"
        allocations[sector] = allocations.get(sector, 0) + w * 100
    return allocations
