"""
Backtesting engine with multiple strategies and comprehensive performance metrics.
"""
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from config import RISK_FREE_RATE, TRADING_DAYS


class BacktestResult:
    def __init__(self, trades: pd.DataFrame, equity: pd.Series, symbol: str, strategy: str):
        self.trades = trades
        self.equity = equity
        self.symbol = symbol
        self.strategy = strategy

    @property
    def metrics(self) -> Dict:
        returns = self.equity.pct_change().dropna()
        total_return = (self.equity.iloc[-1] / self.equity.iloc[0] - 1) * 100
        n_years = len(returns) / TRADING_DAYS
        cagr = ((1 + total_return / 100) ** (1 / n_years) - 1) * 100 if n_years > 0 else total_return
        ann_vol = returns.std() * np.sqrt(TRADING_DAYS) * 100
        sharpe = (returns.mean() - RISK_FREE_RATE / TRADING_DAYS) / (returns.std() or 1e-8) * np.sqrt(TRADING_DAYS)
        downside = returns[returns < 0]
        sortino = (returns.mean() - RISK_FREE_RATE / TRADING_DAYS) / (downside.std() or 1e-8) * np.sqrt(TRADING_DAYS)

        peak = self.equity.cummax()
        dd = (self.equity - peak) / peak
        max_dd = dd.min() * 100
        calmar = abs(cagr / max_dd) if max_dd != 0 else None

        wins = self.trades[self.trades["pnl"] > 0] if len(self.trades) else pd.DataFrame()
        losses = self.trades[self.trades["pnl"] <= 0] if len(self.trades) else pd.DataFrame()
        win_rate = len(wins) / len(self.trades) * 100 if len(self.trades) else 0
        avg_win = wins["pnl"].mean() if len(wins) else 0
        avg_loss = losses["pnl"].mean() if len(losses) else 0
        profit_factor = abs(wins["pnl"].sum() / losses["pnl"].sum()) if len(losses) and losses["pnl"].sum() != 0 else None
        expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss)

        return {
            "strategy": self.strategy,
            "total_return_%": round(total_return, 2),
            "cagr_%": round(cagr, 2),
            "ann_volatility_%": round(ann_vol, 2),
            "sharpe_ratio": round(sharpe, 3),
            "sortino_ratio": round(sortino, 3),
            "calmar_ratio": round(calmar, 3) if calmar else None,
            "max_drawdown_%": round(max_dd, 2),
            "total_trades": len(self.trades),
            "win_rate_%": round(win_rate, 2),
            "avg_win_%": round(avg_win, 3),
            "avg_loss_%": round(avg_loss, 3),
            "profit_factor": round(profit_factor, 3) if profit_factor else None,
            "expectancy_%": round(expectancy, 3),
        }


def run_backtest(
    df: pd.DataFrame,
    signals: pd.Series,
    initial_capital: float = 10000.0,
    commission: float = 0.001,
    symbol: str = "UNKNOWN",
    strategy: str = "Custom",
    stop_loss_pct: Optional[float] = None,
    take_profit_pct: Optional[float] = None,
) -> BacktestResult:
    """
    Run a vectorized backtest on a signal series.

    signals: pd.Series aligned with df, values in {-1, 0, 1}
    """
    prices = df["close"].copy()
    n = len(prices)
    cash = initial_capital
    shares = 0.0
    equity = pd.Series(index=df.index, dtype=float)
    trades = []
    entry_price = None
    entry_date = None
    position = 0

    for i in range(len(df)):
        date = df.index[i]
        price = float(prices.iloc[i])
        sig = int(signals.iloc[i]) if i < len(signals) else 0

        # Stop loss / take profit
        if position != 0 and entry_price is not None:
            if stop_loss_pct and position == 1:
                if price <= entry_price * (1 - stop_loss_pct):
                    sig = -1
            if take_profit_pct and position == 1:
                if price >= entry_price * (1 + take_profit_pct):
                    sig = -1

        # Execute trade
        if sig == 1 and position == 0:
            # Buy
            max_shares = cash / (price * (1 + commission))
            shares = max_shares
            cost = shares * price * (1 + commission)
            cash -= cost
            position = 1
            entry_price = price
            entry_date = date

        elif sig == -1 and position == 1:
            # Sell
            proceeds = shares * price * (1 - commission)
            pnl_pct = (price / entry_price - 1) * 100 if entry_price else 0
            trades.append({
                "entry_date": entry_date,
                "exit_date": date,
                "entry_price": entry_price,
                "exit_price": price,
                "pnl": pnl_pct,
                "duration_days": (date - entry_date).days if hasattr(date, "year") else i,
            })
            cash += proceeds
            shares = 0
            position = 0
            entry_price = None

        equity.iloc[i] = cash + shares * price

    # Close any open position at end
    if position == 1 and shares > 0:
        last_price = float(prices.iloc[-1])
        proceeds = shares * last_price * (1 - commission)
        pnl_pct = (last_price / entry_price - 1) * 100 if entry_price else 0
        trades.append({
            "entry_date": entry_date,
            "exit_date": df.index[-1],
            "entry_price": entry_price,
            "exit_price": last_price,
            "pnl": pnl_pct,
            "duration_days": (df.index[-1] - entry_date).days if hasattr(df.index[-1], "year") else 0,
            "open": True,
        })
        cash += proceeds

    trades_df = pd.DataFrame(trades) if trades else pd.DataFrame(
        columns=["entry_date", "exit_date", "entry_price", "exit_price", "pnl", "duration_days"]
    )
    return BacktestResult(trades_df, equity, symbol, strategy)


# ─── Strategy Signal Generators ──────────────────────────────────────────────

def sma_crossover_signals(df: pd.DataFrame, fast: int = 20, slow: int = 50) -> pd.Series:
    """Buy when fast SMA crosses above slow SMA, sell on cross below."""
    fast_ma = df["close"].rolling(fast).mean()
    slow_ma = df["close"].rolling(slow).mean()
    signals = pd.Series(0, index=df.index)
    signals[fast_ma > slow_ma] = 1
    signals[fast_ma <= slow_ma] = -1
    # Only signal on crossover
    cross = signals.diff().fillna(0)
    buy = cross > 0
    sell = cross < 0
    result = pd.Series(0, index=df.index)
    result[buy] = 1
    result[sell] = -1
    return result


def rsi_signals(df: pd.DataFrame, period: int = 14, oversold: float = 30, overbought: float = 70) -> pd.Series:
    """Buy on RSI oversold, sell on overbought."""
    delta = df["close"].diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rsi = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))

    signals = pd.Series(0, index=df.index)
    buy_signal = (rsi < oversold) & (rsi.shift(1) >= oversold)
    sell_signal = (rsi > overbought) & (rsi.shift(1) <= overbought)
    signals[buy_signal] = 1
    signals[sell_signal] = -1
    return signals


def macd_signals(df: pd.DataFrame) -> pd.Series:
    """Buy on MACD histogram turning positive, sell on negative."""
    fast = df["close"].ewm(span=12, adjust=False).mean()
    slow = df["close"].ewm(span=26, adjust=False).mean()
    macd_line = fast - slow
    signal = macd_line.ewm(span=9, adjust=False).mean()
    hist = macd_line - signal

    signals = pd.Series(0, index=df.index)
    signals[(hist > 0) & (hist.shift(1) <= 0)] = 1
    signals[(hist < 0) & (hist.shift(1) >= 0)] = -1
    return signals


def bollinger_band_signals(df: pd.DataFrame, period: int = 20, std: float = 2) -> pd.Series:
    """Buy below lower band, sell above upper band."""
    sma = df["close"].rolling(period).mean()
    std_dev = df["close"].rolling(period).std()
    upper = sma + std * std_dev
    lower = sma - std * std_dev

    signals = pd.Series(0, index=df.index)
    signals[df["close"] < lower] = 1
    signals[df["close"] > upper] = -1
    return signals


def mean_reversion_signals(df: pd.DataFrame, window: int = 20, z_threshold: float = 2.0) -> pd.Series:
    """Z-score mean reversion strategy."""
    mean = df["close"].rolling(window).mean()
    std = df["close"].rolling(window).std()
    z = (df["close"] - mean) / std.replace(0, np.nan)

    signals = pd.Series(0, index=df.index)
    signals[(z < -z_threshold) & (z.shift(1) >= -z_threshold)] = 1
    signals[(z > z_threshold) & (z.shift(1) <= z_threshold)] = -1
    return signals


def buy_and_hold_signals(df: pd.DataFrame) -> pd.Series:
    """Always in the market."""
    signals = pd.Series(0, index=df.index)
    signals.iloc[0] = 1
    return signals


def run_all_strategies(
    df: pd.DataFrame,
    symbol: str = "TICKER",
    initial_capital: float = 10000.0,
) -> Dict[str, BacktestResult]:
    """Run all built-in strategies and return results."""
    strategies = {
        "Buy & Hold": buy_and_hold_signals(df),
        "SMA 20/50": sma_crossover_signals(df, 20, 50),
        "SMA 50/200": sma_crossover_signals(df, 50, 200),
        "RSI Mean Reversion": rsi_signals(df),
        "MACD Momentum": macd_signals(df),
        "Bollinger Band": bollinger_band_signals(df),
        "Mean Reversion Z": mean_reversion_signals(df),
    }
    results = {}
    for name, signals in strategies.items():
        try:
            result = run_backtest(
                df, signals,
                initial_capital=initial_capital,
                symbol=symbol,
                strategy=name,
                stop_loss_pct=0.08,
            )
            results[name] = result
        except Exception as e:
            pass
    return results


def compare_strategies(results: Dict[str, BacktestResult]) -> pd.DataFrame:
    """Create a comparison DataFrame of all strategy metrics."""
    rows = []
    for name, result in results.items():
        m = result.metrics
        rows.append(m)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if "strategy" in df.columns:
        df = df.set_index("strategy")
    return df.sort_values("sharpe_ratio", ascending=False) if "sharpe_ratio" in df.columns else df
