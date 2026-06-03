"""
Machine Learning price prediction with Random Forest, Gradient Boosting,
and an ensemble model. Includes feature engineering, cross-validation,
and confidence intervals.
"""
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_percentage_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from config import ML_LOOKBACK, ML_FORECAST_DAYS, TRADING_DAYS


def engineer_features(df: pd.DataFrame, indicators: Dict[str, pd.Series]) -> pd.DataFrame:
    """Build feature matrix from price data and technical indicators."""
    feat = pd.DataFrame(index=df.index)

    # Price-derived features
    close = df["close"]
    feat["log_return_1"] = np.log(close / close.shift(1))
    feat["log_return_2"] = np.log(close / close.shift(2))
    feat["log_return_5"] = np.log(close / close.shift(5))
    feat["log_return_10"] = np.log(close / close.shift(10))
    feat["log_return_20"] = np.log(close / close.shift(20))

    for w in [5, 10, 20, 50]:
        feat[f"vol_{w}"] = feat["log_return_1"].rolling(w).std()
        feat[f"sma_ratio_{w}"] = close / close.rolling(w).mean()
        feat[f"price_momentum_{w}"] = close.pct_change(w)

    feat["high_low_ratio"] = df["high"] / df["low"]
    feat["close_high_ratio"] = close / df["high"]
    feat["close_low_ratio"] = close / df["low"]
    feat["body_size"] = (close - df["open"]).abs() / close
    feat["upper_shadow"] = (df["high"] - pd.concat([close, df["open"]], axis=1).max(axis=1)) / close
    feat["lower_shadow"] = (pd.concat([close, df["open"]], axis=1).min(axis=1) - df["low"]) / close

    vol_avg = df["volume"].rolling(20).mean()
    feat["volume_ratio"] = df["volume"] / vol_avg.replace(0, np.nan)
    feat["vol_price_trend"] = feat["log_return_1"] * feat["volume_ratio"]

    # From pre-computed indicators
    indicator_keys = [
        "rsi_14", "rsi_7", "macd", "macd_signal", "macd_hist",
        "bb_width", "bb_pct_b", "atr_14", "adx", "cci_20",
        "mfi_14", "cmf_20", "stoch_k", "stoch_d",
        "williams_r", "roc_12", "tsi", "uo", "ao",
        "vi_plus", "vi_minus", "aroon_osc",
        "zscore_20",
    ]
    for key in indicator_keys:
        if key in indicators:
            feat[key] = indicators[key]

    # Day-of-week and month (cyclical encoding)
    if hasattr(df.index, "dayofweek"):
        dow = df.index.dayofweek
        feat["dow_sin"] = np.sin(2 * np.pi * dow / 5)
        feat["dow_cos"] = np.cos(2 * np.pi * dow / 5)
        month = df.index.month
        feat["month_sin"] = np.sin(2 * np.pi * month / 12)
        feat["month_cos"] = np.cos(2 * np.pi * month / 12)

    return feat


def prepare_dataset(
    df: pd.DataFrame,
    features: pd.DataFrame,
    horizon: int = 5,
    lookback: int = ML_LOOKBACK,
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare (X, y) for supervised learning.
    Target: forward return over `horizon` days.
    """
    target = df["close"].pct_change(horizon).shift(-horizon)
    combined = features.join(target.rename("target")).dropna()

    # Remove infinite values
    combined = combined.replace([np.inf, -np.inf], np.nan).dropna()

    feat_cols = [c for c in combined.columns if c != "target"]
    X = combined[feat_cols].values
    y = combined["target"].values
    return X, y, feat_cols


def train_models(
    X: np.ndarray, y: np.ndarray
) -> Tuple[Dict, Dict]:
    """Train RF, GBM, and Ridge models with time-series CV."""
    models = {
        "rf": Pipeline([
            ("scaler", StandardScaler()),
            ("model", RandomForestRegressor(
                n_estimators=200, max_depth=8, min_samples_leaf=5,
                max_features=0.7, random_state=42, n_jobs=-1
            )),
        ]),
        "gbm": Pipeline([
            ("scaler", StandardScaler()),
            ("model", GradientBoostingRegressor(
                n_estimators=200, learning_rate=0.05, max_depth=5,
                subsample=0.8, min_samples_leaf=5, random_state=42
            )),
        ]),
        "ridge": Pipeline([
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=1.0)),
        ]),
    }

    tscv = TimeSeriesSplit(n_splits=5)
    cv_scores = {}
    trained = {}

    for name, pipeline in models.items():
        scores = []
        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            pipeline.fit(X_train, y_train)
            preds = pipeline.predict(X_val)
            mape = mean_absolute_percentage_error(y_val + 1, preds + 1)
            scores.append(mape)
        cv_scores[name] = np.mean(scores)
        pipeline.fit(X, y)
        trained[name] = pipeline

    return trained, cv_scores


def predict_with_confidence(
    models: Dict,
    cv_scores: Dict,
    X_latest: np.ndarray,
    current_price: float,
    horizon: int,
    n_bootstrap: int = 500,
) -> Dict:
    """
    Ensemble prediction with confidence intervals via bootstrap.
    Weights models by inverse CV error.
    """
    weights = {}
    total_inv = sum(1 / (s + 1e-8) for s in cv_scores.values())
    for name, score in cv_scores.items():
        weights[name] = (1 / (score + 1e-8)) / total_inv

    # Individual model predictions
    individual = {}
    for name, model in models.items():
        pred = float(model.predict(X_latest.reshape(1, -1))[0])
        individual[name] = pred

    # Weighted ensemble
    ensemble_return = sum(weights[name] * individual[name] for name in models)
    predicted_price = current_price * (1 + ensemble_return)

    # Bootstrap confidence interval (using the RF model's tree variability)
    rf_model = models.get("rf")
    if rf_model and hasattr(rf_model.named_steps.get("model", rf_model), "estimators_"):
        estimator = rf_model.named_steps["model"]
        scaler = rf_model.named_steps["scaler"]
        X_scaled = scaler.transform(X_latest.reshape(1, -1))
        tree_preds = np.array([
            tree.predict(X_scaled)[0]
            for tree in estimator.estimators_
        ])
        ci_lower = np.percentile(tree_preds, 5) * current_price + current_price
        ci_upper = np.percentile(tree_preds, 95) * current_price + current_price
        std_dev = np.std(tree_preds) * current_price
    else:
        std_dev = abs(predicted_price - current_price) * 0.3
        ci_lower = predicted_price - 1.96 * std_dev
        ci_upper = predicted_price + 1.96 * std_dev

    direction = "UP" if ensemble_return > 0 else "DOWN"
    confidence = min(abs(ensemble_return) / 0.05 * 50 + 50, 95)

    return {
        "predicted_return": ensemble_return * 100,
        "predicted_price": predicted_price,
        "current_price": current_price,
        "upside": (predicted_price / current_price - 1) * 100,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "std_dev": std_dev,
        "direction": direction,
        "confidence": confidence,
        "horizon_days": horizon,
        "model_weights": weights,
        "individual_predictions": {k: current_price * (1 + v) for k, v in individual.items()},
        "cv_scores": cv_scores,
    }


def feature_importance(models: Dict, feature_names: List[str]) -> pd.DataFrame:
    """Extract and rank feature importances from tree models."""
    importance_dfs = []
    for name in ["rf", "gbm"]:
        if name not in models:
            continue
        model_step = models[name].named_steps.get("model")
        if model_step and hasattr(model_step, "feature_importances_"):
            imp = pd.DataFrame({
                "feature": feature_names,
                f"importance_{name}": model_step.feature_importances_,
            })
            importance_dfs.append(imp.set_index("feature"))

    if not importance_dfs:
        return pd.DataFrame()

    combined = importance_dfs[0]
    for df in importance_dfs[1:]:
        combined = combined.join(df, how="outer").fillna(0)

    imp_cols = [c for c in combined.columns if c.startswith("importance_")]
    combined["mean_importance"] = combined[imp_cols].mean(axis=1)
    return combined.sort_values("mean_importance", ascending=False).head(20)


def multi_horizon_forecast(
    df: pd.DataFrame,
    indicators: Dict[str, pd.Series],
    horizons: List[int] = [5, 10, 20, 30],
) -> Dict[int, Dict]:
    """Run predictions for multiple horizons."""
    features = engineer_features(df, indicators)
    results = {}

    for horizon in horizons:
        try:
            X, y, feat_cols = prepare_dataset(df, features, horizon=horizon)
            if len(X) < 100:
                continue

            models, cv_scores = train_models(X, y)
            X_latest = features.iloc[-1:].fillna(0).replace([np.inf, -np.inf], 0).values
            result = predict_with_confidence(
                models, cv_scores, X_latest,
                float(df["close"].iloc[-1]),
                horizon,
            )
            result["feature_importance"] = feature_importance(models, feat_cols)
            results[horizon] = result
        except Exception as e:
            results[horizon] = {"error": str(e)}

    return results
