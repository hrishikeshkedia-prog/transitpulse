"""
Rich terminal display helpers: panels, tables, progress, color coding.
"""
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text
from rich import box
from rich.columns import Columns
from rich.rule import Rule
from rich.align import Align

console = Console()

# ─── Color helpers ──────────────────────────────────────────────────────────

def color_value(val: float, positive_is_good: bool = True) -> str:
    """Return rich markup color for a numeric value."""
    if val is None:
        return "[dim]N/A[/dim]"
    if positive_is_good:
        color = "green" if val > 0 else "red" if val < 0 else "white"
    else:
        color = "red" if val > 0 else "green" if val < 0 else "white"
    return f"[{color}]{val:+.2f}[/{color}]"


def format_large_number(val: Optional[float], suffix: str = "") -> str:
    if val is None:
        return "N/A"
    if abs(val) >= 1e12:
        return f"{val/1e12:.2f}T{suffix}"
    elif abs(val) >= 1e9:
        return f"{val/1e9:.2f}B{suffix}"
    elif abs(val) >= 1e6:
        return f"{val/1e6:.2f}M{suffix}"
    elif abs(val) >= 1e3:
        return f"{val/1e3:.2f}K{suffix}"
    else:
        return f"{val:.2f}{suffix}"


def pct(val: Optional[float], decimals: int = 2) -> str:
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}%"


def color_signal(signal: str) -> str:
    colors = {
        "STRONG BUY": "bold bright_green",
        "BUY": "green",
        "HOLD": "yellow",
        "SELL": "red",
        "STRONG SELL": "bold bright_red",
    }
    color = colors.get(signal, "white")
    return f"[{color}]{signal}[/{color}]"


def color_sentiment(sentiment: str) -> str:
    colors = {
        "Very Positive": "bold bright_green",
        "Positive": "green",
        "Neutral": "yellow",
        "Negative": "red",
        "Very Negative": "bold bright_red",
    }
    color = colors.get(sentiment, "white")
    return f"[{color}]{sentiment}[/{color}]"


def progress_bar(val: float, max_val: float = 100, width: int = 20, color: str = "green") -> str:
    filled = int(min(val / max_val, 1.0) * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{color}]{bar}[/{color}]"


# ─── Header / Banner ────────────────────────────────────────────────────────

def print_banner():
    banner = """
 ██████╗ ████████╗ ██████╗  ██████╗██╗  ██╗    ██████╗ ██████╗  ██████╗
██╔════╝ ╚══██╔══╝██╔═══██╗██╔════╝██║ ██╔╝    ██╔══██╗██╔══██╗██╔═══██╗
╚█████╗     ██║   ██║   ██║██║     █████╔╝     ██████╔╝██████╔╝██║   ██║
 ╚═══██╗    ██║   ██║   ██║██║     ██╔═██╗     ██╔═══╝ ██╔══██╗██║   ██║
██████╔╝    ██║   ╚██████╔╝╚██████╗██║  ██╗    ██║     ██║  ██║╚██████╔╝
╚═════╝     ╚═╝    ╚═════╝  ╚═════╝╚═╝  ╚═╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝
"""
    console.print(f"[bold cyan]{banner}[/bold cyan]")
    console.print(Align.center("[bold white]Advanced Stock Analyzer[/bold white] [dim]v2.0[/dim]"))
    console.print(Align.center("[dim]Technical • Fundamental • ML Predictions • Portfolio Optimization[/dim]"))
    console.print()


def print_section(title: str, style: str = "bold cyan"):
    console.print()
    console.print(Rule(f"[{style}]{title}[/{style}]", style="dim"))


# ─── Price Summary ───────────────────────────────────────────────────────────

def print_price_summary(info: Dict, df_latest_row):
    symbol = info.get("symbol", "N/A")
    name = info.get("longName", info.get("shortName", "N/A"))
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")
    exchange = info.get("exchange", "N/A")
    currency = info.get("currency", "USD")

    price = info.get("currentPrice") or info.get("regularMarketPrice") or float(df_latest_row["close"])
    prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose") or float(df_latest_row["open"])
    change = price - prev_close
    change_pct = (change / prev_close * 100) if prev_close else 0
    change_color = "green" if change >= 0 else "red"
    change_arrow = "▲" if change >= 0 else "▼"

    w52_high = info.get("fiftyTwoWeekHigh")
    w52_low = info.get("fiftyTwoWeekLow")
    dist_from_high = ((price / w52_high) - 1) * 100 if w52_high else None
    dist_from_low = ((price / w52_low) - 1) * 100 if w52_low else None

    left = Table.grid(padding=(0, 2))
    left.add_column(style="dim")
    left.add_column()
    left.add_row("Symbol:", f"[bold white]{symbol}[/bold white]")
    left.add_row("Name:", f"[bold]{name}[/bold]")
    left.add_row("Exchange:", exchange)
    left.add_row("Sector:", sector)
    left.add_row("Industry:", industry)

    right = Table.grid(padding=(0, 2))
    right.add_column(style="dim")
    right.add_column()
    right.add_row("Price:", f"[bold white]{currency} {price:,.2f}[/bold white]")
    right.add_row("Change:", f"[{change_color}]{change_arrow} {change:+.2f} ({change_pct:+.2f}%)[/{change_color}]")
    right.add_row("52W High:", f"{currency} {w52_high:,.2f}" + (f" [dim]({dist_from_high:+.1f}%)[/dim]" if dist_from_high else "") if w52_high else "N/A")
    right.add_row("52W Low:", f"{currency} {w52_low:,.2f}" + (f" [dim]({dist_from_low:+.1f}%)[/dim]" if dist_from_low else "") if w52_low else "N/A")
    right.add_row("Market Cap:", format_large_number(info.get("marketCap")))

    console.print(Panel(
        Columns([left, right], equal=True),
        title=f"[bold cyan]Stock Overview[/bold cyan]",
        border_style="cyan",
    ))


# ─── Technical Analysis Display ─────────────────────────────────────────────

def print_technical_summary(indicators: Dict, signals_result: Dict, df_last):
    close = float(df_last["close"])
    last = -1

    def iv(key):
        s = indicators.get(key)
        return float(s.iloc[last]) if s is not None and not s.empty and not pd.isna(s.iloc[last]) else None

    import pandas as pd

    # ── Momentum Table ──
    mom_table = Table(title="Momentum Indicators", box=box.ROUNDED, border_style="cyan", show_header=True)
    mom_table.add_column("Indicator", style="dim")
    mom_table.add_column("Value", justify="right")
    mom_table.add_column("Signal", justify="center")

    def rsi_signal(v):
        if v is None: return "N/A"
        if v < 30: return "[green]Oversold ↑[/green]"
        if v > 70: return "[red]Overbought ↓[/red]"
        return "[yellow]Neutral[/yellow]"

    rsi14 = iv("rsi_14")
    rsi7 = iv("rsi_7")
    macd_v = iv("macd")
    macd_s = iv("macd_signal")
    macd_h = iv("macd_hist")
    stoch_k = iv("stoch_k")
    stoch_d = iv("stoch_d")
    cci20 = iv("cci_20")
    wr = iv("williams_r")
    mfi14 = iv("mfi_14")
    adx_v = iv("adx")

    mom_table.add_row("RSI(14)", f"{rsi14:.2f}" if rsi14 else "N/A", rsi_signal(rsi14))
    mom_table.add_row("RSI(7)", f"{rsi7:.2f}" if rsi7 else "N/A", rsi_signal(rsi7))
    mom_table.add_row("MACD", f"{macd_v:.4f}" if macd_v else "N/A",
        "[green]Bullish[/green]" if macd_h and macd_h > 0 else "[red]Bearish[/red]" if macd_h else "N/A")
    mom_table.add_row("MACD Hist", f"{macd_h:.4f}" if macd_h else "N/A",
        "[green]+[/green]" if macd_h and macd_h > 0 else "[red]-[/red]" if macd_h else "N/A")
    mom_table.add_row("Stoch %K/%D", f"{stoch_k:.1f}/{stoch_d:.1f}" if stoch_k and stoch_d else "N/A",
        "[green]Oversold[/green]" if stoch_k and stoch_k < 20 else "[red]Overbought[/red]" if stoch_k and stoch_k > 80 else "[yellow]Normal[/yellow]" if stoch_k else "N/A")
    mom_table.add_row("CCI(20)", f"{cci20:.1f}" if cci20 else "N/A",
        "[green]Oversold[/green]" if cci20 and cci20 < -100 else "[red]Overbought[/red]" if cci20 and cci20 > 100 else "[yellow]Normal[/yellow]" if cci20 else "N/A")
    mom_table.add_row("Williams %R", f"{wr:.1f}" if wr else "N/A",
        "[green]Oversold[/green]" if wr and wr < -80 else "[red]Overbought[/red]" if wr and wr > -20 else "[yellow]Normal[/yellow]" if wr else "N/A")
    mom_table.add_row("MFI(14)", f"{mfi14:.1f}" if mfi14 else "N/A",
        "[green]Oversold[/green]" if mfi14 and mfi14 < 20 else "[red]Overbought[/red]" if mfi14 and mfi14 > 80 else "[yellow]Normal[/yellow]" if mfi14 else "N/A")
    mom_table.add_row("ADX", f"{adx_v:.1f}" if adx_v else "N/A",
        "[green]Strong[/green]" if adx_v and adx_v > 25 else "[yellow]Weak[/yellow]" if adx_v else "N/A")

    # ── Trend Table ──
    trend_table = Table(title="Moving Averages & Trend", box=box.ROUNDED, border_style="blue", show_header=True)
    trend_table.add_column("MA", style="dim")
    trend_table.add_column("Value", justify="right")
    trend_table.add_column("vs Price", justify="center")

    for period in [9, 20, 50, 100, 200]:
        sma_v = iv(f"sma_{period}")
        ema_v = iv(f"ema_{period}")
        if sma_v:
            diff = (close / sma_v - 1) * 100
            color = "green" if close > sma_v else "red"
            trend_table.add_row(
                f"SMA({period})", f"{sma_v:,.2f}",
                f"[{color}]{diff:+.2f}%[/{color}]"
            )
        if ema_v:
            diff = (close / ema_v - 1) * 100
            color = "green" if close > ema_v else "red"
            trend_table.add_row(
                f"EMA({period})", f"{ema_v:,.2f}",
                f"[{color}]{diff:+.2f}%[/{color}]"
            )

    vwap_v = iv("vwap")
    if vwap_v:
        diff = (close / vwap_v - 1) * 100
        color = "green" if close > vwap_v else "red"
        trend_table.add_row("VWAP", f"{vwap_v:,.2f}", f"[{color}]{diff:+.2f}%[/{color}]")

    # ── Signal Summary ──
    composite = signals_result.get("composite", 0)
    rec = signals_result.get("recommendation", "HOLD")
    bar_width = 30
    center = bar_width // 2
    pos = int(composite * center)
    bar_chars = list("─" * bar_width)
    marker_pos = center + pos
    marker_pos = max(0, min(bar_width - 1, marker_pos))
    bar_chars[marker_pos] = "●"
    bar_str = "".join(bar_chars)

    signal_panel = Panel(
        f"""[dim]Bearish[/dim] [red]{bar_str[:center]}[/red][white]{bar_str[center]}[/white][green]{bar_str[center+1:]}[/green] [dim]Bullish[/dim]

[bold]Composite Score:[/bold] {composite:+.3f}  |  [bold]Recommendation:[/bold] {color_signal(rec)}

[dim]Trend:[/dim] {signals_result.get('category_scores', {}).get('trend', 0):+.2f}  [dim]Momentum:[/dim] {signals_result.get('category_scores', {}).get('momentum', 0):+.2f}  [dim]Volume:[/dim] {signals_result.get('category_scores', {}).get('volume', 0):+.2f}  [dim]Volatility:[/dim] {signals_result.get('category_scores', {}).get('volatility', 0):+.2f}""",
        title="[bold yellow]Signal Summary[/bold yellow]",
        border_style="yellow",
    )

    console.print(Columns([mom_table, trend_table], equal=True))
    console.print(signal_panel)


# ─── Fundamental Display ─────────────────────────────────────────────────────

def print_fundamental_summary(ratios: Dict, scores: Dict, dcf: Dict):
    val_table = Table(title="Valuation", box=box.ROUNDED, border_style="magenta", show_header=True)
    val_table.add_column("Metric", style="dim")
    val_table.add_column("Value", justify="right")
    val_table.add_column("Assessment", justify="center")

    def add_row(table, label, val, score_key=None):
        val_str = f"{val:.2f}" if isinstance(val, float) and val else str(val or "N/A")
        score_info = scores.get(score_key, ("N/A", 3)) if score_key else ("", 0)
        score_label = score_info[0] if isinstance(score_info, tuple) else score_info
        score_num = score_info[1] if isinstance(score_info, tuple) else 3
        colors = {5: "bright_green", 4: "green", 3: "yellow", 2: "orange1", 1: "red"}
        color = colors.get(score_num, "white")
        table.add_row(label, val_str, f"[{color}]{score_label}[/{color}]" if score_label else "")

    pe = ratios.get("pe_ratio")
    add_row(val_table, "P/E (TTM)", pe, "pe_score")
    fpe = ratios.get("forward_pe")
    add_row(val_table, "P/E (Forward)", fpe)
    add_row(val_table, "PEG Ratio", ratios.get("peg_ratio"), "peg_score")
    add_row(val_table, "P/B Ratio", ratios.get("price_to_book"))
    add_row(val_table, "P/S Ratio", ratios.get("price_to_sales"))
    add_row(val_table, "EV/EBITDA", ratios.get("ev_ebitda"))

    health_table = Table(title="Financial Health", box=box.ROUNDED, border_style="green", show_header=True)
    health_table.add_column("Metric", style="dim")
    health_table.add_column("Value", justify="right")
    health_table.add_column("Assessment", justify="center")

    roe = ratios.get("return_on_equity")
    add_row(health_table, "ROE", f"{roe*100:.1f}%" if roe else None, "roe_score")
    roa = ratios.get("return_on_assets")
    add_row(health_table, "ROA", f"{roa*100:.1f}%" if roa else None)
    margin = ratios.get("profit_margins")
    add_row(health_table, "Net Margin", f"{margin*100:.1f}%" if margin else None, "margin_score")
    op_margin = ratios.get("operating_margins")
    add_row(health_table, "Operating Margin", f"{op_margin*100:.1f}%" if op_margin else None)
    add_row(health_table, "D/E Ratio", ratios.get("debt_to_equity"), "de_score")
    add_row(health_table, "Current Ratio", ratios.get("current_ratio"), "liquidity_score")
    rg = ratios.get("revenue_growth")
    add_row(health_table, "Revenue Growth", f"{rg*100:.1f}%" if rg else None, "growth_score")
    eg = ratios.get("earnings_growth")
    add_row(health_table, "Earnings Growth", f"{eg*100:.1f}%" if eg else None)

    console.print(Columns([val_table, health_table], equal=True))

    # DCF Valuation
    if dcf:
        intrinsic = dcf.get("intrinsic_value")
        current = dcf.get("current_price")
        upside = dcf.get("upside")
        mos = dcf.get("margin_of_safety")
        if upside is not None:
            color = "green" if upside > 10 else "red" if upside < -10 else "yellow"
            console.print(Panel(
                f"[bold]DCF Intrinsic Value:[/bold] ${intrinsic:.2f}   [bold]Current Price:[/bold] ${current:.2f}\n"
                f"[bold]Upside:[/bold] [{color}]{upside:+.1f}%[/{color}]   "
                f"[bold]Margin of Safety:[/bold] [{color}]{mos:+.1f}%[/{color}]\n"
                f"[dim]Growth Rate Used: {dcf.get('growth_rate_used', 0)*100:.1f}%  |  Discount Rate: {dcf.get('discount_rate', 0)*100:.1f}%[/dim]",
                title="[bold magenta]DCF Valuation[/bold magenta]",
                border_style="magenta",
            ))

    # Overall grade
    grade = scores.get("overall_grade", "N/A")
    score_num = scores.get("overall_score", 0)
    grade_colors = {"A+": "bright_green", "A": "green", "B+": "cyan", "B": "blue", "C+": "yellow", "C": "orange1", "D": "red"}
    g_color = grade_colors.get(grade, "white")
    console.print(Panel(
        f"[bold]Fundamental Grade: [{g_color}]{grade}[/{g_color}][/bold]  (Score: {score_num:.2f}/5.0)",
        border_style=g_color,
        expand=False,
    ))


# ─── Risk Display ────────────────────────────────────────────────────────────

def print_risk_summary(risk: Dict):
    risk_table = Table(title="Risk Metrics", box=box.ROUNDED, border_style="red", show_header=True)
    risk_table.add_column("Metric", style="dim")
    risk_table.add_column("Value", justify="right")
    risk_table.add_column("Assessment", justify="center")

    def risk_row(label, val, fmt=".2f", good_threshold=None, bad_threshold=None, reverse=False):
        if val is None:
            risk_table.add_row(label, "N/A", "")
            return
        val_str = f"{val:{fmt}}"
        assess = ""
        if good_threshold is not None and bad_threshold is not None:
            if reverse:
                color = "green" if val < good_threshold else "red" if val > bad_threshold else "yellow"
            else:
                color = "green" if val > good_threshold else "red" if val < bad_threshold else "yellow"
            assess = f"[{color}]{'Good' if color == 'green' else 'Warning' if color == 'yellow' else 'Poor'}[/{color}]"
        risk_table.add_row(label, val_str, assess)

    risk_row("Annual Return %", risk.get("annual_return"), ".2f", 10, 0)
    risk_row("Annual Volatility %", risk.get("volatility_annual"), ".2f", None, None)
    risk_row("Max Drawdown %", risk.get("max_drawdown"), ".2f", -10, -30, reverse=True)
    risk_row("Sharpe Ratio", risk.get("sharpe_ratio"), ".3f", 1.0, 0.5)
    risk_row("Sortino Ratio", risk.get("sortino_ratio"), ".3f", 1.5, 0.5)
    risk_row("Calmar Ratio", risk.get("calmar_ratio"), ".3f", 1.0, 0.3)
    risk_row("Win Rate %", risk.get("win_rate"), ".1f", 55, 45)
    risk_row("Avg Win %", risk.get("avg_win"), ".3f", 0.5, 0)
    risk_row("Avg Loss %", risk.get("avg_loss"), ".3f", None, None)
    risk_row("VaR 95% (daily)", risk.get("var_95_historical"), ".3f")
    risk_row("CVaR 95% (daily)", risk.get("cvar_95"), ".3f")
    risk_row("VaR 99% (daily)", risk.get("var_99_historical"), ".3f")
    risk_row("Skewness", risk.get("skewness"), ".3f")
    risk_row("Kurtosis", risk.get("kurtosis"), ".3f")

    beta_table = Table(box=box.ROUNDED, border_style="yellow", show_header=True)
    beta_table.add_column("Benchmark Metric", style="dim")
    beta_table.add_column("Value", justify="right")

    beta = risk.get("beta")
    alpha = risk.get("alpha_annual")
    ir = risk.get("information_ratio")
    corr = risk.get("correlation_to_market")

    if beta is not None:
        beta_table.add_row("Beta vs Market", f"{beta:.3f}")
        beta_table.add_row("Alpha (Annual %)", f"{alpha:+.2f}%" if alpha else "N/A")
        beta_table.add_row("Treynor Ratio", f"{risk.get('treynor_ratio', 0):.3f}" if risk.get('treynor_ratio') else "N/A")
        beta_table.add_row("Info Ratio", f"{ir:.3f}" if ir else "N/A")
        beta_table.add_row("Correlation to Market", f"{corr:.3f}" if corr else "N/A")

    console.print(Columns([risk_table, beta_table] if beta is not None else [risk_table], equal=True))


# ─── ML Prediction Display ───────────────────────────────────────────────────

def print_ml_predictions(predictions: Dict):
    ml_table = Table(title="ML Price Predictions", box=box.ROUNDED, border_style="bright_blue", show_header=True)
    ml_table.add_column("Horizon", style="dim")
    ml_table.add_column("Current", justify="right")
    ml_table.add_column("Predicted", justify="right")
    ml_table.add_column("Expected Return", justify="right")
    ml_table.add_column("Direction", justify="center")
    ml_table.add_column("Confidence", justify="right")
    ml_table.add_column("95% CI", justify="right")

    for horizon, result in sorted(predictions.items()):
        if "error" in result:
            ml_table.add_row(f"{horizon}d", "—", "—", "Error", str(result["error"])[:30], "—", "—")
            continue
        current = result.get("current_price", 0)
        pred = result.get("predicted_price", 0)
        ret = result.get("upside", 0)
        direction = result.get("direction", "?")
        conf = result.get("confidence", 0)
        ci_lo = result.get("ci_lower", 0)
        ci_hi = result.get("ci_upper", 0)

        ret_color = "green" if ret > 0 else "red"
        dir_color = "green" if direction == "UP" else "red"

        ml_table.add_row(
            f"{horizon}d",
            f"${current:.2f}",
            f"${pred:.2f}",
            f"[{ret_color}]{ret:+.2f}%[/{ret_color}]",
            f"[{dir_color}]{direction}[/{dir_color}]",
            f"{conf:.0f}%",
            f"[dim]${ci_lo:.2f}–${ci_hi:.2f}[/dim]",
        )

    console.print(ml_table)

    # Model weights
    first = next(iter(predictions.values()), {})
    weights = first.get("model_weights", {})
    if weights:
        w_text = "  ".join(f"[dim]{k}:[/dim] {v:.1%}" for k, v in weights.items())
        console.print(f"[dim]Ensemble weights → {w_text}[/dim]")


# ─── Spinner context ─────────────────────────────────────────────────────────

def make_spinner(description: str):
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        transient=True,
    )
