"""
Risk analysis: VaR, CVaR, drawdown, Sharpe, Sortino, Calmar, Beta, Alpha.
"""
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from config import RISK_FREE_RATE, TRADING_DAYS, VAR_CONFIDENCE, CVAR_CONFIDENCE


def compute_returns(df: pd.DataFrame, log: bool = False) -> pd.Series:
    if log:
        return np.log(df["close"] / df["close"].shift(1)).dropna()
    return df["close"].pct_change().dropna()


def var(returns: pd.Series, confidence: float = VAR_CONFIDENCE) -> float:
    """Historical Value at Risk (daily)."""
    return float(np.percentile(returns, (1 - confidence) * 100))


def cvar(returns: pd.Series, confidence: float = CVAR_CONFIDENCE) -> float:
    """Conditional Value at Risk (Expected Shortfall)."""
    var_val = var(returns, confidence)
    tail = returns[returns <= var_val]
    return float(tail.mean()) if len(tail) > 0 else var_val


def parametric_var(returns: pd.Series, confidence: float = VAR_CONFIDENCE) -> float:
    """Parametric (Gaussian) VaR."""
    mu = returns.mean()
    sigma = returns.std()
    z = stats.norm.ppf(1 - confidence)
    return float(mu + z * sigma)


def monte_carlo_var(
    returns: pd.Series, confidence: float = VAR_CONFIDENCE, simulations: int = 10000, horizon: int = 1
) -> float:
    """Monte Carlo VaR simulation."""
    mu = returns.mean()
    sigma = returns.std()
    sims = np.random.normal(mu * horizon, sigma * np.sqrt(horizon), simulations)
    return float(np.percentile(sims, (1 - confidence) * 100))


def max_drawdown(df: pd.DataFrame) -> Dict[str, float]:
    """Maximum drawdown, duration, and recovery metrics."""
    prices = df["close"]
    peak = prices.cummax()
    drawdown = (prices - peak) / peak
    max_dd = float(drawdown.min())
    max_dd_date = str(drawdown.idxmin().date() if hasattr(drawdown.idxmin(), "date") else drawdown.idxmin())

    # Find the peak before the trough
    trough_idx = drawdown.idxmin()
    peak_idx = prices[:trough_idx].idxmax()
    duration = (trough_idx - peak_idx).days if hasattr(trough_idx, "days") else int(len(prices[peak_idx:trough_idx]))

    # Recovery (how far from trough back to peak)
    post_trough = prices[trough_idx:]
    recovery_idx = post_trough[post_trough >= float(prices[peak_idx])].index
    if len(recovery_idx) > 0:
        recovery_days = (recovery_idx[0] - trough_idx).days if hasattr(recovery_idx[0], "days") else int(len(post_trough[:recovery_idx[0]]))
    else:
        recovery_days = None

    # Calmar ratio
    annual_return = compute_annual_return(df)
    calmar = abs(annual_return / max_dd) if max_dd != 0 else None

    return {
        "max_drawdown": max_dd * 100,
        "max_drawdown_date": max_dd_date,
        "duration_days": duration,
        "recovery_days": recovery_days,
        "calmar_ratio": calmar,
    }


def compute_annual_return(df: pd.DataFrame) -> float:
    """Annualized return."""
    total_return = (df["close"].iloc[-1] / df["close"].iloc[0]) - 1
    years = len(df) / TRADING_DAYS
    if years <= 0:
        return total_return
    return float((1 + total_return) ** (1 / years) - 1)


def sharpe_ratio(
    returns: pd.Series, risk_free: float = RISK_FREE_RATE, trading_days: int = TRADING_DAYS
) -> float:
    """Annualized Sharpe Ratio."""
    daily_rf = risk_free / trading_days
    excess = returns - daily_rf
    if excess.std() == 0:
        return 0.0
    return float(excess.mean() / excess.std() * np.sqrt(trading_days))


def sortino_ratio(
    returns: pd.Series, risk_free: float = RISK_FREE_RATE, trading_days: int = TRADING_DAYS
) -> float:
    """Sortino Ratio — penalizes only downside volatility."""
    daily_rf = risk_free / trading_days
    excess = returns - daily_rf
    downside = returns[returns < 0]
    if len(downside) == 0 or downside.std() == 0:
        return 0.0
    return float(excess.mean() / downside.std() * np.sqrt(trading_days))


def treynor_ratio(
    returns: pd.Series, beta: float, risk_free: float = RISK_FREE_RATE, trading_days: int = TRADING_DAYS
) -> Optional[float]:
    """Treynor Ratio."""
    if beta == 0:
        return None
    annual_excess = (returns.mean() - risk_free / trading_days) * trading_days
    return float(annual_excess / beta)


def information_ratio(returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Information Ratio vs benchmark."""
    active = returns - benchmark_returns.reindex(returns.index).fillna(0)
    if active.std() == 0:
        return 0.0
    return float(active.mean() / active.std() * np.sqrt(TRADING_DAYS))


def beta_alpha(
    returns: pd.Series,
    market_returns: pd.Series,
    risk_free: float = RISK_FREE_RATE,
) -> Tuple[float, float]:
    """OLS regression Beta and Jensen's Alpha."""
    aligned = pd.concat([returns, market_returns], axis=1).dropna()
    if len(aligned) < 10:
        return 1.0, 0.0
    y = aligned.iloc[:, 0].values
    x = aligned.iloc[:, 1].values
    slope, intercept, r_val, p_val, std_err = stats.linregress(x, y)
    beta = float(slope)
    daily_rf = risk_free / TRADING_DAYS
    alpha_daily = float(intercept)
    alpha_annual = alpha_daily * TRADING_DAYS * 100  # in %
    return beta, alpha_annual


def rolling_metrics(df: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    """Rolling Sharpe, Volatility, and Beta (vs SPY if available)."""
    returns = compute_returns(df)
    rolling_sharpe = returns.rolling(window).apply(
        lambda x: sharpe_ratio(pd.Series(x)) if x.std() > 0 else 0
    )
    rolling_vol = returns.rolling(window).std() * np.sqrt(TRADING_DAYS) * 100
    return pd.DataFrame({"rolling_sharpe": rolling_sharpe, "rolling_vol": rolling_vol})


def comprehensive_risk_report(
    df: pd.DataFrame, benchmark_df: Optional[pd.DataFrame] = None
) -> Dict:
    """Full risk metrics report."""
    returns = compute_returns(df)
    log_returns = compute_returns(df, log=True)

    report = {}

    # VaR metrics
    report["var_95_historical"] = var(returns, 0.95) * 100
    report["var_99_historical"] = var(returns, 0.99) * 100
    report["cvar_95"] = cvar(returns, 0.95) * 100
    report["cvar_99"] = cvar(returns, 0.99) * 100
    report["var_95_parametric"] = parametric_var(returns, 0.95) * 100
    report["var_95_mc"] = monte_carlo_var(returns, 0.95) * 100

    # Drawdown
    dd = max_drawdown(df)
    report.update(dd)

    # Return metrics
    report["annual_return"] = compute_annual_return(df) * 100
    report["total_return"] = ((df["close"].iloc[-1] / df["close"].iloc[0]) - 1) * 100
    report["volatility_daily"] = returns.std() * 100
    report["volatility_annual"] = returns.std() * np.sqrt(TRADING_DAYS) * 100
    report["skewness"] = float(stats.skew(returns.dropna()))
    report["kurtosis"] = float(stats.kurtosis(returns.dropna()))

    # Risk-adjusted returns
    report["sharpe_ratio"] = sharpe_ratio(returns)
    report["sortino_ratio"] = sortino_ratio(returns)

    # Positive/negative days
    pos_days = (returns > 0).sum()
    total_days = len(returns)
    report["win_rate"] = float(pos_days / total_days * 100) if total_days > 0 else 0
    report["avg_win"] = float(returns[returns > 0].mean() * 100) if (returns > 0).any() else 0
    report["avg_loss"] = float(returns[returns < 0].mean() * 100) if (returns < 0).any() else 0
    profit_factor = abs(report["avg_win"] / report["avg_loss"]) if report["avg_loss"] != 0 else None
    report["profit_factor"] = profit_factor

    # Benchmark comparison
    if benchmark_df is not None:
        bm_returns = compute_returns(benchmark_df)
        beta_val, alpha_val = beta_alpha(returns, bm_returns)
        report["beta"] = beta_val
        report["alpha_annual"] = alpha_val
        report["treynor_ratio"] = treynor_ratio(returns, beta_val)
        report["information_ratio"] = information_ratio(returns, bm_returns)
        report["correlation_to_market"] = float(
            returns.corr(bm_returns.reindex(returns.index).fillna(0))
        )
    else:
        report["beta"] = None
        report["alpha_annual"] = None

    # Tail risk
    report["tail_ratio"] = float(
        abs(np.percentile(returns, 95)) / abs(np.percentile(returns, 5))
    ) if np.percentile(returns, 5) != 0 else None

    return report
