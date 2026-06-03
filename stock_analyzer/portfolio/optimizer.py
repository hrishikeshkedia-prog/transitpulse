"""
Portfolio optimization: Markowitz, Max Sharpe, Min Variance, Risk Parity.
"""
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from config import RISK_FREE_RATE, TRADING_DAYS


def _port_return(weights, mean_returns):
    return np.dot(weights, mean_returns) * TRADING_DAYS


def _port_vol(weights, cov_matrix):
    return np.sqrt(weights @ cov_matrix @ weights * TRADING_DAYS)


def _neg_sharpe(weights, mean_returns, cov_matrix, rf=RISK_FREE_RATE):
    ret = _port_return(weights, mean_returns)
    vol = _port_vol(weights, cov_matrix)
    if vol == 0:
        return 0
    return -(ret - rf) / vol


def _port_variance(weights, cov_matrix):
    return weights @ cov_matrix @ weights * TRADING_DAYS


def _risk_parity_objective(weights, cov_matrix):
    """Minimize variance of risk contributions."""
    port_var = weights @ cov_matrix @ weights
    marginal = cov_matrix @ weights
    risk_contrib = weights * marginal / (port_var + 1e-10)
    target = np.ones(len(weights)) / len(weights)
    return float(np.sum((risk_contrib - target) ** 2))


def optimize(
    returns: pd.DataFrame,
    method: str = "max_sharpe",
    constraints: Optional[Dict] = None,
    allow_short: bool = False,
) -> Dict:
    """
    Portfolio optimization.

    Methods:
        - max_sharpe: Maximize Sharpe Ratio
        - min_variance: Minimize Portfolio Variance
        - risk_parity: Equal Risk Contribution
        - equal_weight: Naive 1/N
        - max_return: Maximum return for given risk tolerance
    """
    n = len(returns.columns)
    mean_returns = returns.mean()
    cov_matrix = returns.cov()

    cov_np = cov_matrix.values
    mean_np = mean_returns.values

    # Constraints
    bounds = ((-1.0, 1.0) if allow_short else (0.0, 1.0),) * n
    eq_constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]

    if constraints:
        max_single = constraints.get("max_single_weight", 1.0)
        bounds = ((0.0 if not allow_short else -max_single, max_single),) * n
        min_single = constraints.get("min_single_weight", 0.0)
        bounds = ((min_single, max_single),) * n

    init_weights = np.ones(n) / n

    if method == "equal_weight":
        weights = init_weights
        label = "Equal Weight (1/N)"

    elif method == "max_sharpe":
        result = minimize(
            _neg_sharpe,
            init_weights,
            args=(mean_np, cov_np),
            method="SLSQP",
            bounds=bounds,
            constraints=eq_constraints,
            options={"maxiter": 1000, "ftol": 1e-9},
        )
        weights = result.x
        label = "Maximum Sharpe Ratio"

    elif method == "min_variance":
        result = minimize(
            _port_variance,
            init_weights,
            args=(cov_np,),
            method="SLSQP",
            bounds=bounds,
            constraints=eq_constraints,
            options={"maxiter": 1000, "ftol": 1e-9},
        )
        weights = result.x
        label = "Minimum Variance"

    elif method == "risk_parity":
        result = minimize(
            _risk_parity_objective,
            init_weights,
            args=(cov_np,),
            method="SLSQP",
            bounds=bounds,
            constraints=eq_constraints,
            options={"maxiter": 2000, "ftol": 1e-10},
        )
        weights = result.x
        label = "Risk Parity"

    elif method == "max_return":
        result = minimize(
            lambda w: -_port_return(w, mean_np),
            init_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=eq_constraints,
            options={"maxiter": 1000},
        )
        weights = result.x
        label = "Maximum Return"

    else:
        raise ValueError(f"Unknown optimization method: {method}")

    weights = np.clip(weights, 0, 1)
    weights /= weights.sum()

    port_ret = _port_return(weights, mean_np)
    port_vol = _port_vol(weights, cov_np)
    port_sharpe = (port_ret - RISK_FREE_RATE) / port_vol if port_vol > 0 else 0

    weight_dict = {sym: round(float(w), 4) for sym, w in zip(returns.columns, weights)}

    return {
        "method": label,
        "weights": weight_dict,
        "expected_annual_return": port_ret * 100,
        "expected_annual_volatility": port_vol * 100,
        "sharpe_ratio": float(port_sharpe),
    }


def efficient_frontier(
    returns: pd.DataFrame, n_portfolios: int = 100
) -> pd.DataFrame:
    """Generate the efficient frontier by sampling return targets."""
    n = len(returns.columns)
    mean_returns = returns.mean().values
    cov_matrix = returns.cov().values

    bounds = ((0.0, 1.0),) * n
    eq_constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]

    min_ret = min(mean_returns) * TRADING_DAYS
    max_ret = max(mean_returns) * TRADING_DAYS
    target_returns = np.linspace(min_ret, max_ret, n_portfolios)

    results = []
    for target in target_returns:
        constraints = eq_constraints + [
            {"type": "eq", "fun": lambda w, t=target: _port_return(w, mean_returns) - t}
        ]
        try:
            res = minimize(
                _port_variance,
                np.ones(n) / n,
                args=(cov_matrix,),
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
                options={"maxiter": 500},
            )
            if res.success:
                w = res.x / res.x.sum()
                vol = _port_vol(w, cov_matrix)
                ret = _port_return(w, mean_returns)
                sharpe = (ret - RISK_FREE_RATE) / vol if vol > 0 else 0
                results.append({"return": ret * 100, "volatility": vol * 100, "sharpe": sharpe})
        except Exception:
            continue

    return pd.DataFrame(results)


def compare_strategies(returns: pd.DataFrame) -> pd.DataFrame:
    """Compare all optimization strategies side by side."""
    methods = ["equal_weight", "max_sharpe", "min_variance", "risk_parity"]
    rows = []
    for method in methods:
        try:
            result = optimize(returns, method=method)
            rows.append({
                "Strategy": result["method"],
                "Return %": round(result["expected_annual_return"], 2),
                "Volatility %": round(result["expected_annual_volatility"], 2),
                "Sharpe": round(result["sharpe_ratio"], 3),
            })
        except Exception as e:
            rows.append({"Strategy": method, "Error": str(e)})
    return pd.DataFrame(rows)
