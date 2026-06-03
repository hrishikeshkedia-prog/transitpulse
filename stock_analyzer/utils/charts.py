"""
Chart generation using Plotly for interactive HTML charts and Matplotlib for static.
"""
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from config import REPORTS_DIR


def candlestick_with_indicators(
    df: pd.DataFrame,
    indicators: Dict[str, pd.Series],
    symbol: str,
    output_path: Optional[Path] = None,
) -> Path:
    """Generate interactive candlestick chart with indicators."""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        return _fallback_chart(df, symbol, output_path)

    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.50, 0.15, 0.15, 0.20],
        subplot_titles=(f"{symbol} Price", "Volume", "RSI", "MACD"),
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"],
        name="OHLC", increasing_line_color="#26a69a", decreasing_line_color="#ef5350"
    ), row=1, col=1)

    # Moving averages
    colors_ma = {"sma_20": "#fb8c00", "sma_50": "#ab47bc", "ema_20": "#42a5f5", "sma_200": "#ef5350"}
    for key, color in colors_ma.items():
        if key in indicators:
            fig.add_trace(go.Scatter(
                x=df.index, y=indicators[key], name=key.upper(),
                line=dict(color=color, width=1.2), opacity=0.9
            ), row=1, col=1)

    # Bollinger Bands
    if "bb_upper" in indicators and "bb_lower" in indicators:
        fig.add_trace(go.Scatter(
            x=df.index, y=indicators["bb_upper"], name="BB Upper",
            line=dict(color="rgba(100,149,237,0.5)", width=1), showlegend=False
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=indicators["bb_lower"], name="BB Lower",
            fill="tonexty", fillcolor="rgba(100,149,237,0.07)",
            line=dict(color="rgba(100,149,237,0.5)", width=1), showlegend=False
        ), row=1, col=1)

    # Volume
    colors_vol = ["#26a69a" if c >= o else "#ef5350" for c, o in zip(df["close"], df["open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["volume"], name="Volume",
        marker_color=colors_vol, opacity=0.7
    ), row=2, col=1)
    if "vol_sma_20" in indicators:
        fig.add_trace(go.Scatter(
            x=df.index, y=indicators["vol_sma_20"], name="Vol SMA20",
            line=dict(color="orange", width=1.5)
        ), row=2, col=1)

    # RSI
    if "rsi_14" in indicators:
        fig.add_trace(go.Scatter(
            x=df.index, y=indicators["rsi_14"], name="RSI(14)",
            line=dict(color="#7c4dff", width=1.5)
        ), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.3, row=3, col=1)

    # MACD
    if "macd" in indicators and "macd_signal" in indicators and "macd_hist" in indicators:
        hist = indicators["macd_hist"]
        hist_colors = ["#26a69a" if v >= 0 else "#ef5350" for v in hist]
        fig.add_trace(go.Bar(
            x=df.index, y=hist, name="MACD Hist",
            marker_color=hist_colors, opacity=0.7
        ), row=4, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=indicators["macd"], name="MACD",
            line=dict(color="#42a5f5", width=1.5)
        ), row=4, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=indicators["macd_signal"], name="Signal",
            line=dict(color="#ff7043", width=1.5)
        ), row=4, col=1)

    fig.update_layout(
        title=dict(text=f"{symbol} — Technical Analysis Dashboard", font_size=20),
        height=900,
        template="plotly_dark",
        showlegend=True,
        legend=dict(orientation="h", y=1.02, x=0),
        xaxis_rangeslider_visible=False,
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#16213e",
        font=dict(color="#e0e0e0"),
    )

    path = output_path or REPORTS_DIR / f"{symbol}_chart.html"
    fig.write_html(str(path))
    return path


def correlation_heatmap(corr_matrix: pd.DataFrame, symbols: List[str], output_path: Optional[Path] = None) -> Path:
    try:
        import plotly.figure_factory as ff
        import plotly.graph_objects as go
    except ImportError:
        return _save_text_file("Correlation heatmap requires plotly", output_path)

    z = corr_matrix.values
    x = list(corr_matrix.columns)
    y = list(corr_matrix.index)

    fig = go.Figure(data=go.Heatmap(
        z=z, x=x, y=y,
        colorscale="RdYlGn",
        zmin=-1, zmax=1,
        text=[[f"{v:.2f}" for v in row] for row in z],
        texttemplate="%{text}",
        textfont={"size": 12},
        hoverongaps=False,
    ))

    fig.update_layout(
        title="Portfolio Correlation Matrix",
        height=600,
        template="plotly_dark",
        paper_bgcolor="#1a1a2e",
    )

    path = output_path or REPORTS_DIR / "correlation_heatmap.html"
    fig.write_html(str(path))
    return path


def efficient_frontier_chart(frontier: pd.DataFrame, portfolios: Dict, output_path: Optional[Path] = None) -> Path:
    try:
        import plotly.graph_objects as go
    except ImportError:
        return _save_text_file("Plotly required", output_path)

    fig = go.Figure()

    # Efficient frontier line
    if not frontier.empty:
        fig.add_trace(go.Scatter(
            x=frontier["volatility"], y=frontier["return"],
            mode="lines+markers",
            name="Efficient Frontier",
            marker=dict(size=4, color=frontier["sharpe"], colorscale="Viridis", showscale=True,
                        colorbar=dict(title="Sharpe")),
            line=dict(color="lightblue", width=1),
        ))

    # Optimal portfolios
    colors = {"max_sharpe": "gold", "min_variance": "lime", "risk_parity": "orange", "equal_weight": "cyan"}
    for name, result in portfolios.items():
        if "expected_annual_volatility" in result:
            fig.add_trace(go.Scatter(
                x=[result["expected_annual_volatility"]],
                y=[result["expected_annual_return"]],
                mode="markers",
                name=result.get("method", name),
                marker=dict(size=14, symbol="star", color=colors.get(name, "white")),
            ))

    fig.update_layout(
        title="Efficient Frontier & Optimal Portfolios",
        xaxis_title="Annual Volatility (%)",
        yaxis_title="Annual Return (%)",
        height=600,
        template="plotly_dark",
        paper_bgcolor="#1a1a2e",
    )

    path = output_path or REPORTS_DIR / "efficient_frontier.html"
    fig.write_html(str(path))
    return path


def equity_curves(backtest_results: Dict, df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    try:
        import plotly.graph_objects as go
    except ImportError:
        return _save_text_file("Plotly required", output_path)

    fig = go.Figure()
    colors_list = ["#42a5f5", "#66bb6a", "#ffa726", "#ef5350", "#ab47bc", "#26c6da", "#8d6e63"]

    for i, (name, result) in enumerate(backtest_results.items()):
        equity = result.equity.dropna()
        normalized = (equity / equity.iloc[0]) * 100 if len(equity) > 0 else equity
        color = colors_list[i % len(colors_list)]
        metrics = result.metrics
        sharpe = metrics.get("sharpe_ratio", 0)
        total_ret = metrics.get("total_return_%", 0)
        fig.add_trace(go.Scatter(
            x=equity.index, y=normalized,
            name=f"{name} ({total_ret:+.1f}%, SR:{sharpe:.2f})",
            line=dict(color=color, width=2),
        ))

    fig.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)
    fig.update_layout(
        title="Strategy Equity Curves (Normalized to 100)",
        xaxis_title="Date",
        yaxis_title="Portfolio Value (Normalized)",
        height=600,
        template="plotly_dark",
        paper_bgcolor="#1a1a2e",
        legend=dict(orientation="h", y=-0.15),
    )

    path = output_path or REPORTS_DIR / "equity_curves.html"
    fig.write_html(str(path))
    return path


def ml_prediction_chart(
    df: pd.DataFrame,
    predictions: Dict,
    symbol: str,
    output_path: Optional[Path] = None,
) -> Path:
    try:
        import plotly.graph_objects as go
    except ImportError:
        return _save_text_file("Plotly required", output_path)

    fig = go.Figure()
    tail = df.tail(90)

    fig.add_trace(go.Scatter(
        x=tail.index, y=tail["close"],
        name="Actual Price", line=dict(color="#42a5f5", width=2),
    ))

    last_date = df.index[-1]
    last_price = float(df["close"].iloc[-1])

    colors_pred = {5: "#66bb6a", 10: "#ffa726", 20: "#ef5350", 30: "#ab47bc"}
    for horizon, result in sorted(predictions.items()):
        if "error" in result or "predicted_price" not in result:
            continue
        future_date = last_date + pd.Timedelta(days=horizon)
        pred_price = result["predicted_price"]
        ci_lo = result.get("ci_lower", pred_price * 0.95)
        ci_hi = result.get("ci_upper", pred_price * 1.05)
        color = colors_pred.get(horizon, "white")

        fig.add_trace(go.Scatter(
            x=[last_date, future_date],
            y=[last_price, pred_price],
            name=f"{horizon}d Pred",
            line=dict(color=color, width=2, dash="dash"),
            mode="lines+markers",
            marker=dict(size=10, symbol="diamond"),
        ))

        fig.add_trace(go.Scatter(
            x=[future_date, future_date],
            y=[ci_lo, ci_hi],
            mode="markers",
            name=f"{horizon}d CI",
            marker=dict(size=8, color=color, symbol="line-ns-open"),
            showlegend=False,
        ))

    fig.update_layout(
        title=f"{symbol} — ML Price Predictions",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=500,
        template="plotly_dark",
        paper_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
    )

    path = output_path or REPORTS_DIR / f"{symbol}_ml_predictions.html"
    fig.write_html(str(path))
    return path


def _save_text_file(text: str, path: Optional[Path]) -> Path:
    p = path or REPORTS_DIR / "chart_error.txt"
    p.write_text(text)
    return p


def _fallback_chart(df: pd.DataFrame, symbol: str, path: Optional[Path]) -> Path:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={"height_ratios": [3, 1]})
    fig.patch.set_facecolor("#1a1a2e")

    ax1.set_facecolor("#16213e")
    ax1.plot(df.index, df["close"], color="#42a5f5", linewidth=1.5, label="Close")
    ax1.fill_between(df.index, df["close"], alpha=0.1, color="#42a5f5")
    ax1.set_title(f"{symbol} Price", color="white", fontsize=14)
    ax1.tick_params(colors="white")
    ax1.legend(facecolor="#1a1a2e", labelcolor="white")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    ax2.set_facecolor("#16213e")
    ax2.bar(df.index, df["volume"], color="#26a69a", alpha=0.7, width=0.8)
    ax2.set_ylabel("Volume", color="white")
    ax2.tick_params(colors="white")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    plt.tight_layout()
    p = path or REPORTS_DIR / f"{symbol}_chart.png"
    plt.savefig(str(p), dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
    plt.close()
    return p
