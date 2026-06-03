#!/usr/bin/env python3
"""
Advanced Stock Analyzer — Main CLI Entry Point.
Combines technical, fundamental, ML, portfolio, and risk analysis
into a single unified interactive terminal application.
"""
import sys
import os
import argparse
import traceback
from pathlib import Path
from typing import Dict, List, Optional

# Add parent dir for imports
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich import box
from rich.columns import Columns

from config import SECTOR_PEERS, REPORTS_DIR
from core.data_fetcher import DataFetcher
from core.technical import compute_all, generate_signals, support_resistance_levels, fibonacci_retracements, pivot_points
from core.fundamental import extract_ratios, dcf_valuation, score_fundamentals, analyze_financials, graham_number
from core.patterns import detect_candlestick_patterns, detect_chart_patterns, detect_divergences, market_regime
from core.risk import comprehensive_risk_report, compute_returns
from core.sentiment import analyze_news
from core.ml_predictor import engineer_features, multi_horizon_forecast
from portfolio.analyzer import build_returns_matrix, individual_metrics, portfolio_performance, correlation_matrix
from portfolio.optimizer import optimize, compare_strategies as optimizer_compare, efficient_frontier
from portfolio.backtest import run_all_strategies, compare_strategies as backtest_compare
from utils.display import (
    console, print_banner, print_section, print_price_summary,
    print_technical_summary, print_fundamental_summary, print_risk_summary,
    print_ml_predictions, format_large_number, color_signal, color_sentiment,
    progress_bar,
)
from utils.charts import (
    candlestick_with_indicators, correlation_heatmap,
    efficient_frontier_chart, equity_curves, ml_prediction_chart,
)
from reports.generator import generate_html_report


fetcher = DataFetcher()


# ─── Analysis Runner ─────────────────────────────────────────────────────────

def run_full_analysis(
    symbol: str,
    period: str = "1y",
    run_ml: bool = True,
    run_backtest: bool = True,
    generate_report: bool = True,
    generate_charts: bool = True,
    benchmark: str = "^GSPC",
) -> Dict:
    """Run complete analysis pipeline for a single stock."""

    results = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:

        # 1. Fetch data
        task = progress.add_task("[cyan]Fetching price history...", total=None)
        df = fetcher.get_price_history(symbol, period=period)
        results["df"] = df
        progress.update(task, description=f"[green]✓ Fetched {len(df)} bars for {symbol}")

        # 2. Fetch benchmark for risk
        task2 = progress.add_task("[cyan]Fetching benchmark...", total=None)
        try:
            bench_df = fetcher.get_price_history(benchmark, period=period)
        except Exception:
            bench_df = None
        progress.update(task2, description="[green]✓ Benchmark loaded")

        # 3. Company info & fundamentals
        task3 = progress.add_task("[cyan]Fetching company info...", total=None)
        info = fetcher.get_info(symbol)
        financials = fetcher.get_financials(symbol)
        ratios = extract_ratios(info)
        dcf = dcf_valuation(info)
        scores = score_fundamentals(ratios)
        fin_analysis = analyze_financials(financials)
        graham = graham_number(info)
        results.update({"info": info, "ratios": ratios, "dcf": dcf, "scores": scores,
                        "fin_analysis": fin_analysis, "graham": graham})
        progress.update(task3, description="[green]✓ Fundamentals loaded")

        # 4. Technical indicators
        task4 = progress.add_task("[cyan]Computing technical indicators...", total=None)
        indicators = compute_all(df)
        signals_result = generate_signals(df, indicators)
        sr_levels = support_resistance_levels(df)
        fib_levels = fibonacci_retracements(df)
        pivots = pivot_points(df)
        results.update({"indicators": indicators, "signals": signals_result,
                        "sr": sr_levels, "fib": fib_levels, "pivots": pivots})
        progress.update(task4, description=f"[green]✓ {len(indicators)} indicators computed")

        # 5. Pattern detection
        task5 = progress.add_task("[cyan]Detecting chart patterns...", total=None)
        candle_patterns = detect_candlestick_patterns(df)
        chart_patterns = detect_chart_patterns(df)
        rsi_series = indicators.get("rsi_14", pd.Series())
        divergences = detect_divergences(df, rsi_series) if not rsi_series.empty else []
        regime = market_regime(df)
        results.update({"candle_patterns": candle_patterns, "chart_patterns": chart_patterns,
                        "divergences": divergences, "regime": regime})
        progress.update(task5, description=f"[green]✓ {len(candle_patterns)+len(chart_patterns)} patterns detected")

        # 6. Risk analysis
        task6 = progress.add_task("[cyan]Computing risk metrics...", total=None)
        risk = comprehensive_risk_report(df, bench_df)
        results["risk"] = risk
        progress.update(task6, description="[green]✓ Risk metrics computed")

        # 7. News sentiment
        task7 = progress.add_task("[cyan]Fetching news sentiment...", total=None)
        news = fetcher.get_news(symbol)
        news_analysis = analyze_news(news)
        results["news_analysis"] = news_analysis
        progress.update(task7, description=f"[green]✓ {news_analysis['total_articles']} articles analyzed")

        # 8. ML predictions
        if run_ml:
            task8 = progress.add_task("[cyan]Training ML models...", total=None)
            try:
                predictions = multi_horizon_forecast(df, indicators, horizons=[5, 10, 20, 30])
            except Exception as e:
                predictions = {h: {"error": str(e)} for h in [5, 10, 20, 30]}
            results["predictions"] = predictions
            progress.update(task8, description="[green]✓ ML predictions generated")
        else:
            results["predictions"] = {}

        # 9. Backtesting
        if run_backtest:
            task9 = progress.add_task("[cyan]Running backtests...", total=None)
            try:
                backtest_results = run_all_strategies(df, symbol)
                results["backtest_results"] = backtest_results
            except Exception as e:
                results["backtest_results"] = {}
            progress.update(task9, description="[green]✓ Backtests complete")

        # 10. Generate charts
        if generate_charts:
            task10 = progress.add_task("[cyan]Generating charts...", total=None)
            try:
                chart_path = candlestick_with_indicators(df, indicators, symbol)
                results["chart_path"] = chart_path
                if results.get("predictions"):
                    ml_chart = ml_prediction_chart(df, results["predictions"], symbol)
                    results["ml_chart_path"] = ml_chart
            except Exception:
                pass
            if results.get("backtest_results"):
                try:
                    bt_chart = equity_curves(results["backtest_results"], df)
                    results["bt_chart_path"] = bt_chart
                except Exception:
                    pass
            progress.update(task10, description="[green]✓ Charts generated")

        # 11. Generate HTML report
        if generate_report:
            task11 = progress.add_task("[cyan]Generating HTML report...", total=None)
            try:
                report_path = generate_html_report(
                    symbol, info, ratios, scores, dcf, risk, signals_result,
                    results.get("predictions", {}),
                    chart_patterns, candle_patterns, news_analysis, regime,
                )
                results["report_path"] = report_path
            except Exception as e:
                results["report_error"] = str(e)
            progress.update(task11, description="[green]✓ Report generated")

    return results


def display_full_analysis(symbol: str, results: Dict):
    """Display the full analysis results in the terminal."""

    print_section(f"Analysis: {symbol}", "bold cyan")

    # Price Summary
    df = results["df"]
    print_price_summary(results["info"], df.iloc[-1])

    # Market Regime
    regime = results.get("regime", {})
    console.print(Panel(
        f"[bold]Regime:[/bold] [yellow]{regime.get('regime', 'Unknown')}[/yellow]  "
        f"[bold]Volatility:[/bold] {regime.get('volatility_annualized', 0):.1f}% annualized  "
        f"[bold]Trend R²:[/bold] {regime.get('r_squared', 0):.3f}",
        title="[bold]Market Regime[/bold]",
        border_style="dim",
        expand=False,
    ))

    # Technical
    print_section("Technical Analysis")
    print_technical_summary(results["indicators"], results["signals"], df.iloc[-1])

    # Support/Resistance & Fibonacci
    sr = results.get("sr", {})
    fib = results.get("fib", {})
    pivots = results.get("pivots", {})
    current_price = float(df["close"].iloc[-1])

    sr_table = Table(title="Support & Resistance", box=box.ROUNDED, border_style="blue")
    sr_table.add_column("Level", style="dim")
    sr_table.add_column("Price", justify="right")
    sr_table.add_column("Distance", justify="right")

    for name, price_val in pivots.items():
        dist = (price_val / current_price - 1) * 100
        color = "green" if price_val < current_price else "red"
        sr_table.add_row(f"Pivot {name}", f"${price_val:.2f}", f"[{color}]{dist:+.2f}%[/{color}]")

    for price_val in sr.get("resistance", [])[:3]:
        dist = (price_val / current_price - 1) * 100
        sr_table.add_row("[red]Resistance[/red]", f"${price_val:.2f}", f"[red]{dist:+.2f}%[/red]")

    for price_val in sr.get("support", [])[:3]:
        dist = (price_val / current_price - 1) * 100
        sr_table.add_row("[green]Support[/green]", f"${price_val:.2f}", f"[green]{dist:+.2f}%[/green]")

    fib_table = Table(title="Fibonacci Levels", box=box.ROUNDED, border_style="magenta")
    fib_table.add_column("Level", style="dim")
    fib_table.add_column("Price", justify="right")
    fib_table.add_column("Distance", justify="right")

    for level, price_val in sorted(fib.items(), key=lambda x: x[1], reverse=True)[:7]:
        dist = (price_val / current_price - 1) * 100
        color = "green" if price_val < current_price else "red"
        fib_table.add_row(f"Fib {level}", f"${price_val:.2f}", f"[{color}]{dist:+.2f}%[/{color}]")

    console.print(Columns([sr_table, fib_table], equal=True))

    # Patterns
    all_patterns = results.get("candle_patterns", []) + results.get("chart_patterns", []) + results.get("divergences", [])
    if all_patterns:
        print_section("Chart Patterns & Divergences")
        pat_table = Table(box=box.ROUNDED, border_style="yellow")
        pat_table.add_column("Pattern")
        pat_table.add_column("Direction", justify="center")
        pat_table.add_column("Description")

        for p in all_patterns[:10]:
            d = p.get("direction", "neutral")
            color = "green" if d == "bullish" else "red" if d == "bearish" else "yellow"
            pat_table.add_row(p.get("name", p.get("type", "?")),
                              f"[{color}]{d.title()}[/{color}]",
                              p.get("description", ""))
        console.print(pat_table)

    # Fundamental Analysis
    print_section("Fundamental Analysis")
    print_fundamental_summary(results["ratios"], results["scores"], results["dcf"])

    # Show Graham Number
    graham = results.get("graham")
    if graham:
        price_now = float(df["close"].iloc[-1])
        diff = (graham / price_now - 1) * 100
        color = "green" if graham > price_now else "red"
        console.print(f"[dim]Graham Number:[/dim] [bold]${graham:.2f}[/bold]  [dim]vs Price:[/dim] [{color}]{diff:+.1f}%[/{color}]")

    # Risk Analysis
    print_section("Risk Analysis")
    print_risk_summary(results["risk"])

    # Backtest Results
    if results.get("backtest_results"):
        print_section("Strategy Backtesting Results")
        bt_df = backtest_compare(results["backtest_results"])
        if not bt_df.empty:
            # Only show key columns for readability
            key_cols = ["total_return_%", "cagr_%", "sharpe_ratio", "sortino_ratio",
                        "max_drawdown_%", "win_rate_%", "total_trades", "profit_factor"]
            show_cols = [c for c in key_cols if c in bt_df.columns]

            start_date = results["df"].index[0].date() if hasattr(results["df"].index[0], "date") else ""
            end_date = results["df"].index[-1].date() if hasattr(results["df"].index[-1], "date") else ""
            bt_table = Table(
                title=f"Strategy Comparison ({start_date} – {end_date})",
                box=box.ROUNDED, border_style="cyan", show_header=True
            )
            bt_table.add_column("Strategy", style="bold")
            col_labels = {
                "total_return_%": "Return%", "cagr_%": "CAGR%", "sharpe_ratio": "Sharpe",
                "sortino_ratio": "Sortino", "max_drawdown_%": "MaxDD%",
                "win_rate_%": "Win%", "total_trades": "Trades", "profit_factor": "PF",
            }
            for col in show_cols:
                bt_table.add_column(col_labels.get(col, col), justify="right")

            for strategy_name, row in bt_df.iterrows():
                cells = [str(strategy_name)]
                for col in show_cols:
                    val = row.get(col)
                    if val is None or (isinstance(val, float) and pd.isna(val)):
                        cells.append("N/A")
                    elif isinstance(val, float):
                        if "return" in col or "drawdown" in col or "cagr" in col:
                            color = "green" if val > 0 else "red"
                            cells.append(f"[{color}]{val:+.2f}%[/{color}]")
                        elif "sharpe" in col or "sortino" in col:
                            color = "green" if val > 1 else "yellow" if val > 0.5 else "red"
                            cells.append(f"[{color}]{val:.3f}[/{color}]")
                        elif "win_rate" in col:
                            color = "green" if val > 55 else "yellow" if val > 45 else "red"
                            cells.append(f"[{color}]{val:.1f}%[/{color}]")
                        elif "profit_factor" in col:
                            color = "green" if val and val > 1.5 else "yellow" if val and val > 1.0 else "red"
                            cells.append(f"[{color}]{val:.2f}[/{color}]")
                        else:
                            cells.append(f"{val:.2f}")
                    else:
                        cells.append(str(val))
                bt_table.add_row(*cells)

            console.print(bt_table)

    # ML Predictions
    if results.get("predictions"):
        print_section("ML Price Predictions")
        print_ml_predictions(results["predictions"])

    # News Sentiment
    print_section("News Sentiment")
    news = results["news_analysis"]
    score_color = "green" if news["overall_score"] > 0.1 else "red" if news["overall_score"] < -0.1 else "yellow"
    console.print(f"Overall: {color_sentiment(news['overall_sentiment'])} "
                  f"(score: [{score_color}]{news['overall_score']:+.3f}[/{score_color}])  "
                  f"Positive: [green]{news['positive_count']}[/green]  "
                  f"Negative: [red]{news['negative_count']}[/red]  "
                  f"Neutral: [dim]{news['neutral_count']}[/dim]")

    for art in news.get("articles", [])[:5]:
        sent_color = "green" if art["score"] > 0.1 else "red" if art["score"] < -0.1 else "dim"
        console.print(f"  [{sent_color}]•[/{sent_color}] {art['title'][:80]}... [dim]({art['publisher']})[/dim]")

    # Output paths
    print_section("Generated Files")
    if results.get("report_path"):
        console.print(f"[green]HTML Report:[/green] {results['report_path']}")
    if results.get("chart_path"):
        console.print(f"[green]Price Chart:[/green] {results['chart_path']}")
    if results.get("ml_chart_path"):
        console.print(f"[green]ML Chart:[/green] {results['ml_chart_path']}")
    if results.get("bt_chart_path"):
        console.print(f"[green]Backtest Chart:[/green] {results['bt_chart_path']}")


# ─── Portfolio Analysis ──────────────────────────────────────────────────────

def run_portfolio_analysis(symbols: List[str], period: str = "1y"):
    """Run portfolio-level analysis for a list of symbols."""
    print_section(f"Portfolio Analysis: {', '.join(symbols)}")

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), TimeElapsedColumn(), transient=True) as prog:
        task = prog.add_task("[cyan]Fetching portfolio data...", total=None)
        price_dict = fetcher.get_multiple_histories(symbols, period=period)
        prog.update(task, description=f"[green]✓ Loaded {len(price_dict)} symbols")

    if len(price_dict) < 2:
        console.print("[red]Need at least 2 symbols for portfolio analysis[/red]")
        return

    returns = build_returns_matrix(price_dict)
    symbols_loaded = list(returns.columns)

    # Individual metrics
    print_section("Individual Asset Metrics")
    metrics_df = individual_metrics(returns)
    metrics_table = Table(box=box.ROUNDED, border_style="cyan")
    metrics_table.add_column("Symbol", style="bold")
    for col in metrics_df.columns:
        metrics_table.add_column(col, justify="right")

    for sym, row in metrics_df.iterrows():
        cells = [sym]
        for col, val in row.items():
            if "return" in col.lower() or "drawdown" in col.lower():
                color = "green" if val > 0 else "red"
                cells.append(f"[{color}]{val:+.2f}[/{color}]")
            elif "sharpe" in col.lower() or "sortino" in col.lower():
                color = "green" if val > 1 else "yellow" if val > 0.5 else "red"
                cells.append(f"[{color}]{val:.3f}[/{color}]")
            else:
                cells.append(f"{val:.3f}")
        metrics_table.add_row(*cells)
    console.print(metrics_table)

    # Portfolio optimization
    print_section("Portfolio Optimization")
    strategies_table = Table(title="Strategy Comparison", box=box.ROUNDED, border_style="magenta")
    strategies_table.add_column("Strategy")
    strategies_table.add_column("Return %", justify="right")
    strategies_table.add_column("Volatility %", justify="right")
    strategies_table.add_column("Sharpe", justify="right")

    optimal_portfolios = {}
    for method in ["equal_weight", "max_sharpe", "min_variance", "risk_parity"]:
        try:
            result = optimize(returns, method=method)
            optimal_portfolios[method] = result
            ret_color = "green" if result["expected_annual_return"] > 0 else "red"
            sharpe_color = "green" if result["sharpe_ratio"] > 1 else "yellow" if result["sharpe_ratio"] > 0.5 else "red"
            strategies_table.add_row(
                result["method"],
                f"[{ret_color}]{result['expected_annual_return']:+.2f}%[/{ret_color}]",
                f"{result['expected_annual_volatility']:.2f}%",
                f"[{sharpe_color}]{result['sharpe_ratio']:.3f}[/{sharpe_color}]",
            )
        except Exception as e:
            strategies_table.add_row(method, "Error", str(e)[:30], "—")

    console.print(strategies_table)

    # Best portfolio weights
    best = optimal_portfolios.get("max_sharpe")
    if best:
        weights_table = Table(title="Max Sharpe Portfolio Weights", box=box.ROUNDED, border_style="yellow")
        weights_table.add_column("Symbol")
        weights_table.add_column("Weight", justify="right")
        weights_table.add_column("Allocation Bar")

        for sym, w in sorted(best["weights"].items(), key=lambda x: -x[1]):
            bar = progress_bar(w * 100, 100, 20)
            weights_table.add_row(sym, f"{w:.1%}", bar)
        console.print(weights_table)

    # Correlation matrix
    print_section("Correlation Matrix")
    corr = correlation_matrix(returns)
    corr_table = Table(box=box.ROUNDED, border_style="blue")
    corr_table.add_column("", style="bold")
    for sym in symbols_loaded:
        corr_table.add_column(sym, justify="right")

    for sym in symbols_loaded:
        row = [sym]
        for sym2 in symbols_loaded:
            val = corr.loc[sym, sym2]
            if sym == sym2:
                row.append("[dim]1.000[/dim]")
            else:
                color = "red" if val > 0.7 else "yellow" if val > 0.4 else "green"
                row.append(f"[{color}]{val:.3f}[/{color}]")
        corr_table.add_row(*row)
    console.print(corr_table)

    # Generate charts
    try:
        corr_chart = correlation_heatmap(corr, symbols_loaded)
        console.print(f"[green]Correlation Chart:[/green] {corr_chart}")
        ef = efficient_frontier(returns)
        ef_chart = efficient_frontier_chart(ef, optimal_portfolios)
        console.print(f"[green]Efficient Frontier:[/green] {ef_chart}")
    except Exception as e:
        console.print(f"[dim]Chart generation: {e}[/dim]")


# ─── Screener ────────────────────────────────────────────────────────────────

def run_screener(sector: Optional[str] = None, criteria: Optional[Dict] = None):
    """Screen stocks from a predefined universe."""
    print_section("Stock Screener")

    if sector and sector in SECTOR_PEERS:
        universe = SECTOR_PEERS[sector]
    else:
        # Default universe
        universe = sum(SECTOR_PEERS.values(), [])[:20]

    console.print(f"Screening [cyan]{len(universe)}[/cyan] stocks...")

    results = []
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), TimeElapsedColumn(), transient=True) as prog:
        task = prog.add_task(f"[cyan]Screening {len(universe)} stocks...", total=None)
        for sym in universe:
            try:
                info = fetcher.get_info(sym)
                df = fetcher.get_price_history(sym, period="6mo")
                indicators = compute_all(df)
                signals = generate_signals(df, indicators)
                risk = comprehensive_risk_report(df)

                ratios = extract_ratios(info)
                results.append({
                    "symbol": sym,
                    "name": (info.get("shortName", sym) or sym)[:20],
                    "price": info.get("currentPrice") or info.get("regularMarketPrice", 0) or float(df["close"].iloc[-1]),
                    "signal": signals.get("recommendation", "HOLD"),
                    "score": signals.get("composite", 0),
                    "pe": ratios.get("pe_ratio"),
                    "roe": ratios.get("return_on_equity"),
                    "sharpe": risk.get("sharpe_ratio", 0),
                    "return_6m": risk.get("total_return", 0) or ((df["close"].iloc[-1] / df["close"].iloc[0]) - 1) * 100,
                    "volatility": risk.get("volatility_annual", 0),
                })
            except Exception:
                pass
        prog.update(task, description=f"[green]✓ Screened {len(results)} stocks")

    if not results:
        console.print("[red]No results found[/red]")
        return

    # Sort by composite score
    results = sorted(results, key=lambda x: x["score"], reverse=True)

    screen_table = Table(title=f"Screener Results ({sector or 'Mixed'})", box=box.ROUNDED, border_style="cyan")
    screen_table.add_column("Symbol", style="bold")
    screen_table.add_column("Name")
    screen_table.add_column("Price", justify="right")
    screen_table.add_column("Signal", justify="center")
    screen_table.add_column("Score", justify="right")
    screen_table.add_column("P/E", justify="right")
    screen_table.add_column("ROE%", justify="right")
    screen_table.add_column("Sharpe", justify="right")
    screen_table.add_column("6M Return%", justify="right")

    for r in results:
        rec = r["signal"]
        rec_colors = {"STRONG BUY": "bright_green", "BUY": "green", "HOLD": "yellow", "SELL": "red", "STRONG SELL": "bright_red"}
        rec_color = rec_colors.get(rec, "white")
        score_color = "green" if r["score"] > 0.2 else "red" if r["score"] < -0.2 else "yellow"
        ret_color = "green" if r["return_6m"] > 0 else "red"
        roe_str = f"{r['roe']*100:.1f}%" if r['roe'] else "N/A"
        pe_str = f"{r['pe']:.1f}" if r['pe'] and r['pe'] > 0 else "N/A"
        screen_table.add_row(
            r["symbol"], r["name"],
            f"${r['price']:,.2f}",
            f"[{rec_color}]{rec}[/{rec_color}]",
            f"[{score_color}]{r['score']:+.3f}[/{score_color}]",
            pe_str, roe_str,
            f"{r['sharpe']:.2f}",
            f"[{ret_color}]{r['return_6m']:+.1f}%[/{ret_color}]",
        )

    console.print(screen_table)


# ─── Compare Stocks ──────────────────────────────────────────────────────────

def compare_stocks(symbols: List[str], period: str = "1y"):
    """Compare multiple stocks side by side."""
    print_section(f"Comparing: {', '.join(symbols)}")

    rows = []
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), TimeElapsedColumn(), transient=True) as prog:
        task = prog.add_task(f"[cyan]Analyzing {len(symbols)} stocks...", total=None)
        for sym in symbols:
            try:
                info = fetcher.get_info(sym)
                df = fetcher.get_price_history(sym, period=period)
                indicators = compute_all(df)
                signals = generate_signals(df, indicators)
                risk = comprehensive_risk_report(df)
                ratios = extract_ratios(info)
                total_ret = ((df["close"].iloc[-1] / df["close"].iloc[0]) - 1) * 100
                rows.append({
                    "symbol": sym,
                    "price": info.get("currentPrice") or float(df["close"].iloc[-1]),
                    "mktcap": ratios.get("market_cap"),
                    "pe": ratios.get("pe_ratio"),
                    "roe": ratios.get("return_on_equity"),
                    "margin": ratios.get("profit_margins"),
                    "beta": ratios.get("beta"),
                    "sharpe": risk.get("sharpe_ratio", 0),
                    "max_dd": risk.get("max_drawdown", 0),
                    "total_ret": total_ret,
                    "signal": signals.get("recommendation", "HOLD"),
                    "score": signals.get("composite", 0),
                })
            except Exception as e:
                rows.append({"symbol": sym, "error": str(e)})
        prog.update(task, description="[green]✓ Done")

    if not rows:
        return

    cmp_table = Table(title=f"Stock Comparison ({period})", box=box.ROUNDED, border_style="cyan")
    cmp_table.add_column("Symbol", style="bold")
    cmp_table.add_column("Price", justify="right")
    cmp_table.add_column("Mkt Cap", justify="right")
    cmp_table.add_column("P/E", justify="right")
    cmp_table.add_column("ROE%", justify="right")
    cmp_table.add_column("Net Margin%", justify="right")
    cmp_table.add_column("Beta", justify="right")
    cmp_table.add_column("Sharpe", justify="right")
    cmp_table.add_column("Max DD%", justify="right")
    cmp_table.add_column(f"Return ({period})", justify="right")
    cmp_table.add_column("Signal", justify="center")

    for r in rows:
        if "error" in r:
            cmp_table.add_row(r["symbol"], "[red]Error[/red]", *["—"] * 9)
            continue
        roe_str = f"{r['roe']*100:.1f}" if r['roe'] else "N/A"
        margin_str = f"{r['margin']*100:.1f}" if r['margin'] else "N/A"
        pe_str = f"{r['pe']:.1f}" if r['pe'] and r['pe'] > 0 else "N/A"
        ret_color = "green" if r["total_ret"] > 0 else "red"
        dd_color = "red" if r["max_dd"] < -20 else "yellow" if r["max_dd"] < -10 else "green"
        sharpe_color = "green" if r["sharpe"] > 1 else "yellow" if r["sharpe"] > 0.5 else "red"
        rec = r["signal"]
        rec_colors = {"STRONG BUY": "bright_green", "BUY": "green", "HOLD": "yellow", "SELL": "red", "STRONG SELL": "bright_red"}

        cmp_table.add_row(
            r["symbol"],
            f"${r['price']:,.2f}",
            format_large_number(r.get("mktcap")),
            pe_str, roe_str, margin_str,
            f"{r['beta']:.2f}" if r.get("beta") else "N/A",
            f"[{sharpe_color}]{r['sharpe']:.2f}[/{sharpe_color}]",
            f"[{dd_color}]{r['max_dd']:+.1f}%[/{dd_color}]",
            f"[{ret_color}]{r['total_ret']:+.1f}%[/{ret_color}]",
            f"[{rec_colors.get(rec, 'white')}]{rec}[/{rec_colors.get(rec, 'white')}]",
        )

    console.print(cmp_table)


# ─── Interactive Menu ─────────────────────────────────────────────────────────

def interactive_menu():
    """Main interactive menu loop."""
    print_banner()

    while True:
        console.print()
        console.print(Panel(
            """[bold cyan]1.[/bold cyan] Full Stock Analysis
[bold cyan]2.[/bold cyan] Portfolio Analysis & Optimization
[bold cyan]3.[/bold cyan] Compare Multiple Stocks
[bold cyan]4.[/bold cyan] Stock Screener
[bold cyan]5.[/bold cyan] Quick Price & Signal Check
[bold cyan]6.[/bold cyan] Options Chain Analysis
[bold cyan]7.[/bold cyan] Market Overview (Benchmarks)
[bold cyan]0.[/bold cyan] [dim]Exit[/dim]""",
            title="[bold white]Main Menu[/bold white]",
            border_style="cyan",
            expand=False,
        ))

        choice = Prompt.ask("[bold]Select option[/bold]", choices=["0", "1", "2", "3", "4", "5", "6", "7"])

        if choice == "0":
            console.print("[dim]Goodbye![/dim]")
            break

        elif choice == "1":
            symbol = Prompt.ask("[bold]Enter stock symbol[/bold]", default="AAPL").upper().strip()
            period = Prompt.ask("Period", choices=["1mo", "3mo", "6mo", "1y", "2y", "5y"], default="1y")
            run_ml = Confirm.ask("Run ML predictions? (slower)", default=True)
            run_bt = Confirm.ask("Run backtests?", default=True)
            gen_report = Confirm.ask("Generate HTML report?", default=True)

            try:
                results = run_full_analysis(
                    symbol, period=period, run_ml=run_ml,
                    run_backtest=run_bt, generate_report=gen_report,
                )
                display_full_analysis(symbol, results)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                console.print_exception(show_locals=False)

        elif choice == "2":
            symbols_str = Prompt.ask("[bold]Enter symbols (comma-separated)[/bold]", default="AAPL,MSFT,GOOGL,NVDA,AMZN")
            symbols = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]
            period = Prompt.ask("Period", choices=["3mo", "6mo", "1y", "2y"], default="1y")
            try:
                run_portfolio_analysis(symbols, period)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

        elif choice == "3":
            symbols_str = Prompt.ask("[bold]Enter symbols to compare (comma-separated)[/bold]", default="AAPL,MSFT,GOOGL")
            symbols = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]
            period = Prompt.ask("Period", choices=["3mo", "6mo", "1y", "2y"], default="1y")
            try:
                compare_stocks(symbols, period)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

        elif choice == "4":
            sectors = list(SECTOR_PEERS.keys()) + ["All"]
            console.print(f"Available sectors: [cyan]{', '.join(sectors)}[/cyan]")
            sector = Prompt.ask("Enter sector", default="Technology")
            sector = sector if sector in SECTOR_PEERS else None
            try:
                run_screener(sector=sector)
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

        elif choice == "5":
            symbols_str = Prompt.ask("[bold]Enter symbols (comma-separated)[/bold]", default="AAPL,TSLA,NVDA")
            symbols = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]
            for sym in symbols:
                try:
                    df = fetcher.get_price_history(sym, period="3mo")
                    info = fetcher.get_info(sym)
                    indicators = compute_all(df)
                    signals = generate_signals(df, indicators)
                    price = float(df["close"].iloc[-1])
                    rec = signals.get("recommendation", "HOLD")
                    score = signals.get("composite", 0)
                    rsi_val = float(indicators["rsi_14"].iloc[-1]) if "rsi_14" in indicators else None
                    macd_h = float(indicators["macd_hist"].iloc[-1]) if "macd_hist" in indicators else None
                    console.print(
                        f"[bold]{sym}[/bold]  ${price:,.2f}  "
                        f"Signal: {color_signal(rec)} ({score:+.3f})  "
                        f"RSI: {rsi_val:.1f}  " if rsi_val else "",
                        f"MACD Hist: {'[green]+' if macd_h and macd_h > 0 else '[red]'}{macd_h:.4f}[/] " if macd_h else ""
                    )
                except Exception as e:
                    console.print(f"[red]{sym}: {e}[/red]")

        elif choice == "6":
            symbol = Prompt.ask("[bold]Enter symbol for options chain[/bold]", default="AAPL").upper()
            try:
                chain = fetcher.get_options_chain(symbol)
                if chain:
                    console.print(f"Available expirations: [cyan]{', '.join(chain['expirations'][:5])}[/cyan]")
                    for exp, data in list(chain["chains"].items())[:1]:
                        calls = data["calls"]
                        puts = data["puts"]
                        print_section(f"Options Chain: {symbol} (Exp: {exp})")
                        opt_table = Table(title="Calls vs Puts Summary", box=box.ROUNDED, border_style="cyan")
                        opt_table.add_column("Metric")
                        opt_table.add_column("Calls", justify="right")
                        opt_table.add_column("Puts", justify="right")
                        opt_table.add_row("Total OI", f"{calls['openInterest'].sum():,.0f}", f"{puts['openInterest'].sum():,.0f}")
                        opt_table.add_row("Total Volume", f"{calls['volume'].fillna(0).sum():,.0f}", f"{puts['volume'].fillna(0).sum():,.0f}")
                        opt_table.add_row("Avg IV", f"{calls['impliedVolatility'].mean():.2%}", f"{puts['impliedVolatility'].mean():.2%}")
                        console.print(opt_table)

                        # Put/Call ratio
                        pc_ratio = puts["openInterest"].sum() / max(calls["openInterest"].sum(), 1)
                        pc_color = "red" if pc_ratio > 1.0 else "green"
                        console.print(f"Put/Call OI Ratio: [{pc_color}]{pc_ratio:.2f}[/{pc_color}]  "
                                      f"({'Bearish bias' if pc_ratio > 1 else 'Bullish bias'})")
                else:
                    console.print(f"[yellow]No options data available for {symbol}[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

        elif choice == "7":
            print_section("Market Overview")
            try:
                benchmarks = fetcher.get_market_benchmarks(period="1mo")
                mkt_table = Table(title="Market Benchmarks (1 Month)", box=box.ROUNDED, border_style="cyan")
                mkt_table.add_column("Index")
                mkt_table.add_column("Current", justify="right")
                mkt_table.add_column("1M Return", justify="right")
                mkt_table.add_column("1M High", justify="right")
                mkt_table.add_column("1M Low", justify="right")
                mkt_table.add_column("Volatility", justify="right")

                for name, df in benchmarks.items():
                    if df.empty:
                        continue
                    current = float(df["close"].iloc[-1])
                    ret_1m = (current / df["close"].iloc[0] - 1) * 100
                    high_1m = float(df["high"].max())
                    low_1m = float(df["low"].min())
                    vol = df["close"].pct_change().std() * np.sqrt(252) * 100
                    ret_color = "green" if ret_1m > 0 else "red"
                    mkt_table.add_row(
                        name, f"{current:,.2f}",
                        f"[{ret_color}]{ret_1m:+.2f}%[/{ret_color}]",
                        f"{high_1m:,.2f}", f"{low_1m:,.2f}",
                        f"{vol:.1f}%",
                    )
                console.print(mkt_table)

                # Sector ETF performance
                sector_etfs = fetcher.get_sector_etfs()
                sec_table = Table(title="Sector ETFs (1 Month)", box=box.ROUNDED, border_style="magenta")
                sec_table.add_column("ETF")
                sec_table.add_column("Sector")
                sec_table.add_column("Return", justify="right")

                sector_rows = []
                for etf, sector in sector_etfs.items():
                    try:
                        etf_df = fetcher.get_price_history(etf, period="1mo")
                        ret = (float(etf_df["close"].iloc[-1]) / float(etf_df["close"].iloc[0]) - 1) * 100
                        sector_rows.append((etf, sector, ret))
                    except Exception:
                        pass

                for etf, sector, ret in sorted(sector_rows, key=lambda x: -x[2]):
                    color = "green" if ret > 0 else "red"
                    sec_table.add_row(etf, sector, f"[{color}]{ret:+.2f}%[/{color}]")

                console.print(sec_table)

            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Advanced Stock Analyzer — Technical, Fundamental, ML & Portfolio Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Interactive menu
  python main.py analyze AAPL            # Full analysis of AAPL
  python main.py analyze AAPL --period 2y --no-ml
  python main.py compare AAPL MSFT GOOGL
  python main.py portfolio AAPL MSFT NVDA AMZN
  python main.py screen --sector Technology
  python main.py market                   # Market overview
        """,
    )
    parser.add_argument("command", nargs="?", default="menu",
                        choices=["menu", "analyze", "compare", "portfolio", "screen", "market"],
                        help="Command to run")
    parser.add_argument("symbols", nargs="*", help="Stock symbols")
    parser.add_argument("--period", default="1y", help="Data period (default: 1y)")
    parser.add_argument("--no-ml", action="store_true", help="Skip ML predictions")
    parser.add_argument("--no-report", action="store_true", help="Skip HTML report")
    parser.add_argument("--no-charts", action="store_true", help="Skip chart generation")
    parser.add_argument("--no-backtest", action="store_true", help="Skip backtesting")
    parser.add_argument("--sector", default=None, help="Sector for screener")
    parser.add_argument("--benchmark", default="^GSPC", help="Benchmark symbol (default: ^GSPC)")

    args = parser.parse_args()

    if args.command == "menu":
        interactive_menu()

    elif args.command == "analyze":
        symbols = args.symbols or ["AAPL"]
        for symbol in symbols:
            print_banner()
            try:
                results = run_full_analysis(
                    symbol.upper(),
                    period=args.period,
                    run_ml=not args.no_ml,
                    run_backtest=not args.no_backtest,
                    generate_report=not args.no_report,
                    generate_charts=not args.no_charts,
                    benchmark=args.benchmark,
                )
                display_full_analysis(symbol.upper(), results)
            except Exception as e:
                console.print(f"[red]Error analyzing {symbol}: {e}[/red]")
                console.print_exception()

    elif args.command == "compare":
        symbols = args.symbols
        if not symbols:
            console.print("[red]Please provide symbols to compare[/red]")
            sys.exit(1)
        print_banner()
        compare_stocks(symbols, args.period)

    elif args.command == "portfolio":
        symbols = args.symbols
        if not symbols:
            console.print("[red]Please provide portfolio symbols[/red]")
            sys.exit(1)
        print_banner()
        run_portfolio_analysis(symbols, args.period)

    elif args.command == "screen":
        print_banner()
        run_screener(sector=args.sector)

    elif args.command == "market":
        print_banner()
        try:
            benchmarks = fetcher.get_market_benchmarks(period="1mo")
            print_section("Market Overview")
            for name, df in benchmarks.items():
                if df.empty:
                    continue
                ret = (float(df["close"].iloc[-1]) / float(df["close"].iloc[0]) - 1) * 100
                color = "green" if ret > 0 else "red"
                console.print(f"  [bold]{name}:[/bold] [{color}]{ret:+.2f}%[/{color}] (1mo)")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    main()
