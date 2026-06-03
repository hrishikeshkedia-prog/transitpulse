"""
Real-time terminal display using Rich Live.
Bloomberg-style live ticker board, instant quote panels, and global dashboard.
"""
import time
from datetime import datetime
from typing import Dict, List, Optional

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from core.realtime import RealTimeQuote, QuoteFetcher, get_multi_quotes
from core.global_markets import (
    EXCHANGES, MAJOR_INDICES, INDICES_BY_REGION,
    get_currency_symbol, COUNTRY_FLAGS, get_all_open_markets, is_market_open,
)

console = Console()


# ─── Number formatting helpers ───────────────────────────────────────────────

def _fmt_vol(val: Optional[int]) -> str:
    if val is None:
        return "—"
    if val >= 1_000_000_000:
        return f"{val/1_000_000_000:.1f}B"
    if val >= 1_000_000:
        return f"{val/1_000_000:.1f}M"
    if val >= 1_000:
        return f"{val/1_000:.0f}K"
    return str(val)


def _fmt_mktcap(val: Optional[float]) -> str:
    if val is None:
        return "—"
    if val >= 1e12:
        return f"{val/1e12:.2f}T"
    if val >= 1e9:
        return f"{val/1e9:.1f}B"
    if val >= 1e6:
        return f"{val/1e6:.0f}M"
    return f"{val:.0f}"


def _fmt_price(quote: RealTimeQuote) -> str:
    if quote.price is None:
        return "[dim]—[/dim]"
    sym = quote.currency_symbol
    cur = quote.currency
    if cur in ("JPY", "KRW", "IDR", "VND"):
        return f"{sym}{quote.price:,.0f}"
    return f"{sym}{quote.price:,.2f}"


def _change_markup(quote: RealTimeQuote) -> str:
    if quote.change is None or quote.change_pct is None:
        return "[dim]—[/dim]"
    color = "green" if quote.change >= 0 else "red"
    arrow = "▲" if quote.change >= 0 else "▼"
    sym = quote.currency_symbol
    cur = quote.currency
    if cur in ("JPY", "KRW", "IDR"):
        amt = f"{sym}{abs(quote.change):,.0f}"
    else:
        amt = f"{sym}{abs(quote.change):.2f}"
    return f"[{color}]{arrow} {amt} ({quote.change_pct:+.2f}%)[/{color}]"


def _pct_markup(pct: Optional[float]) -> str:
    if pct is None:
        return "[dim]—[/dim]"
    color = "green" if pct >= 0 else "red"
    arrow = "▲" if pct >= 0 else "▼"
    return f"[{color}]{arrow}{abs(pct):.2f}%[/{color}]"


def _status_badge(status: str) -> str:
    badges = {
        "open":    "[bold bright_green]● OPEN[/bold bright_green]",
        "closed":  "[dim]○ CLOSED[/dim]",
        "pre":     "[bold yellow]◐ PRE[/bold yellow]",
        "post":    "[bold cyan]◑ POST[/bold cyan]",
        "unknown": "[dim]? —[/dim]",
    }
    return badges.get(status, f"[dim]{status}[/dim]")


def _asset_color(asset_type: str) -> str:
    colors = {
        "stock": "white", "etf": "cyan", "crypto": "yellow",
        "forex": "blue", "futures": "magenta", "index": "bright_white",
    }
    return colors.get(asset_type, "white")


def _52w_bar(price: float, low_52: float, high_52: float, width: int = 10) -> str:
    """Show where current price sits in the 52-week range as a mini bar."""
    if not all([price, low_52, high_52]) or high_52 == low_52:
        return "[dim]—[/dim]"
    pct = (price - low_52) / (high_52 - low_52)
    pos = max(0, min(int(pct * width), width - 1))
    bar = "─" * pos + "●" + "─" * (width - pos - 1)
    color = "green" if pct > 0.7 else "yellow" if pct > 0.3 else "red"
    return f"[{color}]{bar}[/{color}]"


# ─── Live Ticker Table ────────────────────────────────────────────────────────

def build_live_ticker_table(quotes: Dict[str, RealTimeQuote]) -> Table:
    """Build the main live price table."""
    table = Table(
        box=box.SIMPLE_HEAVY,
        border_style="dim",
        show_header=True,
        header_style="bold dim",
        padding=(0, 1),
        expand=True,
    )
    table.add_column("Symbol", style="bold", no_wrap=True, min_width=10)
    table.add_column("Name", max_width=22, no_wrap=True)
    table.add_column("Price", justify="right", min_width=12, no_wrap=True)
    table.add_column("Change", justify="right", min_width=18, no_wrap=True)
    table.add_column("Vol", justify="right", min_width=7)
    table.add_column("Mkt Cap", justify="right", min_width=8)
    table.add_column("52W Range", justify="center", min_width=12)
    table.add_column("Status", justify="center", min_width=9)
    table.add_column("Upd", justify="right", min_width=5, style="dim")

    for symbol, q in quotes.items():
        color = _asset_color(q.asset_type)
        age = q.age_seconds
        age_str = f"{age:.0f}s" if age < 60 else f"{age/60:.0f}m"
        if q.is_stale:
            age_str = "[red]err[/red]"

        name = (q.name or symbol)[:22]

        # 52W range bar
        range_bar = _52w_bar(q.price or 0, q.year_low or 0, q.year_high or 0)

        # Pre/post market indicator
        extra = ""
        if q.market_status == "pre" and q.pre_market_price:
            sym = q.currency_symbol
            extra = f" [yellow](pre {sym}{q.pre_market_price:,.2f})[/yellow]"
        elif q.market_status == "post" and q.post_market_price:
            sym = q.currency_symbol
            extra = f" [cyan](aft {sym}{q.post_market_price:,.2f})[/cyan]"

        table.add_row(
            f"[{color}]{symbol}[/{color}]",
            f"[dim]{name}[/dim]",
            _fmt_price(q) + extra,
            _change_markup(q),
            _fmt_vol(q.volume),
            _fmt_mktcap(q.market_cap),
            range_bar,
            _status_badge(q.market_status),
            age_str,
        )

    return table


def build_market_status_panel() -> Panel:
    """Shows which major global markets are currently open."""
    open_markets = get_all_open_markets()

    regions = {
        "Americas": ["NYSE", "NASDAQ", "TSX", "B3", "BMV"],
        "Europe":   ["LSE", "XETRA", "ENP", "BME", "MIL", "SIX", "OMX"],
        "Asia":     ["TSE", "HKEX", "SSE", "NSE", "KRX", "SGX", "ASX"],
        "ME/Africa":["TADAWUL", "JSE", "EGX"],
    }

    lines = []
    for region, codes in regions.items():
        parts = []
        for code in codes:
            exch = EXCHANGES.get(code, {})
            flag = exch.get("flag", "")
            if code in open_markets:
                parts.append(f"[green]{flag}{code}[/green]")
            else:
                parts.append(f"[dim]{flag}{code}[/dim]")
        lines.append(f"[bold dim]{region}:[/bold dim] " + "  ".join(parts))

    utc_now = datetime.utcnow().strftime("%H:%M:%S UTC")
    local_now = datetime.now().strftime("%H:%M:%S Local")
    content = "\n".join(lines) + f"\n\n[dim]Time: {utc_now} | {local_now}[/dim]"

    return Panel(content, title="[bold]Global Market Hours[/bold]", border_style="dim", padding=(0, 1))


def build_global_indices_table(quotes: Dict[str, RealTimeQuote]) -> Table:
    """Compact multi-column indices table grouped by region."""
    table = Table(box=box.ROUNDED, border_style="dim", show_header=True,
                  header_style="bold dim", padding=(0, 1))
    table.add_column("Index", no_wrap=True, min_width=16)
    table.add_column("Price", justify="right", min_width=12)
    table.add_column("Change%", justify="right", min_width=9)
    table.add_column("Index", no_wrap=True, min_width=16)
    table.add_column("Price", justify="right", min_width=12)
    table.add_column("Change%", justify="right", min_width=9)

    items = [(name, symbol, quotes.get(symbol)) for name, symbol in MAJOR_INDICES.items()
             if symbol in quotes]

    for i in range(0, len(items), 2):
        row = []
        for j in range(2):
            if i + j < len(items):
                name, sym, q = items[i + j]
                row.extend([
                    f"[dim]{name[:16]}[/dim]",
                    _fmt_price(q) if q else "—",
                    _pct_markup(q.change_pct if q else None),
                ])
            else:
                row.extend(["", "", ""])
        table.add_row(*row)

    return table


# ─── Live Dashboard ───────────────────────────────────────────────────────────

class LiveDashboard:
    """
    Bloomberg-style live terminal dashboard.
    Refreshes all symbol quotes at a configurable interval.
    """

    def __init__(
        self,
        symbols: List[str],
        refresh_interval: float = 5.0,
        show_market_status: bool = True,
    ):
        self.symbols = symbols
        self.refresh_interval = refresh_interval
        self.show_market_status = show_market_status
        self.fetcher = QuoteFetcher(symbols, refresh_interval)
        self._iteration = 0

    def _render(self) -> Group:
        quotes = self.fetcher.get_all_cached()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        header = Panel(
            Align.center(
                f"[bold cyan]⚡ LIVE MARKET FEED[/bold cyan]  "
                f"[dim]{now}[/dim]  "
                f"[dim]Refresh: {self.refresh_interval:.0f}s  |  "
                f"Ctrl+C to exit[/dim]"
            ),
            border_style="cyan",
            padding=(0, 0),
        )

        ticker_table = build_live_ticker_table(quotes) if quotes else Panel("[dim]Loading...[/dim]")

        parts = [header, ticker_table]

        if self.show_market_status:
            parts.append(build_market_status_panel())

        return Group(*parts)

    def run(self, duration: Optional[float] = None):
        """Run the live dashboard. Blocks until Ctrl+C or duration expires."""
        console.print("[dim]Starting live feed... (press Ctrl+C to exit)[/dim]")

        # Initial fetch
        self.fetcher.refresh_now()

        # Start background polling
        self.fetcher.start_polling()

        start = time.time()
        try:
            with Live(
                self._render(),
                refresh_per_second=0.5,
                screen=False,
                console=console,
            ) as live:
                while True:
                    time.sleep(0.5)
                    live.update(self._render())
                    if duration and (time.time() - start) > duration:
                        break
        except KeyboardInterrupt:
            pass
        finally:
            self.fetcher.stop_polling()

        console.print("[dim]Live feed stopped.[/dim]")


# ─── Instant Quote Display ────────────────────────────────────────────────────

def display_instant_quote(quote: RealTimeQuote, intraday: Optional[Dict] = None):
    """Display a full-detail instant quote panel."""
    sym = quote.currency_symbol
    cur = quote.currency

    def p(v):
        if v is None:
            return "[dim]—[/dim]"
        if cur in ("JPY", "KRW", "IDR"):
            return f"{sym}{v:,.0f}"
        return f"{sym}{v:,.2f}"

    # Price block
    price_color = "green" if (quote.change or 0) >= 0 else "red"
    change_arrow = "▲" if (quote.change or 0) >= 0 else "▼"

    left = Table.grid(padding=(0, 2))
    left.add_column(style="dim")
    left.add_column()
    left.add_row("Symbol:", f"[bold white]{quote.symbol}[/bold white]")
    left.add_row("Name:", f"[bold]{(quote.name or quote.symbol)[:40]}[/bold]")
    left.add_row("Exchange:", quote.exchange or "—")
    left.add_row("Asset Type:", quote.asset_type.title())
    left.add_row("Currency:", f"{cur}")
    left.add_row("Market:", _status_badge(quote.market_status))

    right = Table.grid(padding=(0, 2))
    right.add_column(style="dim")
    right.add_column()
    right.add_row("Price:", f"[bold white]{p(quote.price)}[/bold white]")
    right.add_row("Change:", f"[{price_color}]{change_arrow} {p(abs(quote.change or 0))} ({(quote.change_pct or 0):+.2f}%)[/{price_color}]")
    right.add_row("Open:", p(quote.open_))
    right.add_row("High:", f"[green]{p(quote.high)}[/green]")
    right.add_row("Low:", f"[red]{p(quote.low)}[/red]")
    right.add_row("Prev Close:", p(quote.prev_close))

    console.print(Panel(
        Columns([left, right], equal=True),
        title=f"[bold cyan]Live Quote — {quote.symbol}[/bold cyan]",
        border_style="cyan",
    ))

    # Additional details
    details = Table.grid(padding=(0, 3))
    details.add_column(style="dim")
    details.add_column()
    details.add_column(style="dim")
    details.add_column()
    details.add_column(style="dim")
    details.add_column()

    vol_ratio = None
    if quote.volume and quote.avg_volume and quote.avg_volume > 0:
        vol_ratio = quote.volume / quote.avg_volume

    details.add_row(
        "Volume:", _fmt_vol(quote.volume) + (f" [dim]({vol_ratio:.1f}x avg)[/dim]" if vol_ratio else ""),
        "Avg Vol:", _fmt_vol(quote.avg_volume),
        "Mkt Cap:", _fmt_mktcap(quote.market_cap),
    )

    # 52W range
    if quote.year_high and quote.year_low:
        bar = _52w_bar(quote.price or 0, quote.year_low, quote.year_high, width=20)
        pct_from_high = ((quote.price or 0) / quote.year_high - 1) * 100
        pct_from_low = ((quote.price or 0) / quote.year_low - 1) * 100
        details.add_row(
            "52W Low:", p(quote.year_low),
            "52W Pos:", bar,
            "52W High:", p(quote.year_high),
        )
        details.add_row(
            "From High:", f"[red]{pct_from_high:+.1f}%[/red]",
            "", "",
            "From Low:", f"[green]{pct_from_low:+.1f}%[/green]",
        )

    console.print(Panel(details, border_style="dim"))

    # Pre/post market
    if quote.pre_market_price:
        console.print(f"[yellow]Pre-Market:[/yellow] {p(quote.pre_market_price)}  "
                      f"[dim]({(quote.pre_market_change_pct or 0):+.2f}% vs close)[/dim]")
    if quote.post_market_price:
        console.print(f"[cyan]After-Hours:[/cyan] {p(quote.post_market_price)}  "
                      f"[dim]({(quote.post_market_change_pct or 0):+.2f}% vs close)[/dim]")

    # USD equivalent if not USD
    if quote.currency not in ("USD",) and quote.price_usd and quote.usd_rate:
        console.print(f"[dim]USD Equivalent:[/dim] [white]${quote.price_usd:.2f}[/white]  "
                      f"[dim](rate: 1 {quote.currency} = ${quote.usd_rate:.4f})[/dim]")

    # Intraday analysis overlay
    if intraday and "error" not in intraday:
        from rich.rule import Rule
        console.print()
        console.print(Rule("[dim]Intraday Session[/dim]", style="dim"))

        session_chg = intraday.get("session_change_pct")
        vwap = intraday.get("vwap")
        levels = intraday.get("levels", {})

        intra_table = Table.grid(padding=(0, 2))
        intra_table.add_column(style="dim")
        intra_table.add_column()
        intra_table.add_column(style="dim")
        intra_table.add_column()

        chg_color = "green" if (session_chg or 0) > 0 else "red"
        intra_table.add_row(
            "Session:", f"[{chg_color}]{(session_chg or 0):+.2f}%[/{chg_color}]",
            "VWAP:", f"${vwap:.2f}" if vwap else "—",
        )
        intra_table.add_row(
            "OR High:", f"${levels.get('or_high', 0):.2f}" if levels.get('or_high') else "—",
            "OR Low:", f"${levels.get('or_low', 0):.2f}" if levels.get('or_low') else "—",
        )
        intra_table.add_row(
            "Pivot:", f"${levels.get('pivot', 0):.2f}" if levels.get('pivot') else "—",
            "R1/S1:", f"${levels.get('r1', 0):.2f} / ${levels.get('s1', 0):.2f}" if levels.get('r1') else "—",
        )
        console.print(intra_table)

        # Intraday patterns
        patterns = intraday.get("patterns", [])
        if patterns:
            for p_item in patterns[:4]:
                d = p_item.get("direction", "neutral")
                color = "green" if d == "bullish" else "red" if d == "bearish" else "yellow"
                console.print(f"  [{color}]◆[/{color}] [bold]{p_item['name']}[/bold]  [dim]{p_item.get('description', '')}[/dim]")

    console.print(f"\n[dim]Updated: {quote.last_updated.strftime('%H:%M:%S')}[/dim]")


def display_search_results(results: List[Dict]):
    """Display symbol search results in a Rich table."""
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    table = Table(
        title="[bold]Global Symbol Search Results[/bold]",
        box=box.ROUNDED, border_style="cyan", show_header=True
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Symbol", style="bold", min_width=12)
    table.add_column("Name", min_width=30)
    table.add_column("Exchange", min_width=25)
    table.add_column("Type", justify="center")
    table.add_column("Currency")
    table.add_column("Country", justify="center")

    type_colors = {
        "stock": "white", "etf": "cyan", "crypto": "yellow",
        "forex": "blue", "futures": "magenta", "index": "bright_white",
    }

    for i, r in enumerate(results, 1):
        asset = r.get("asset_type", "stock")
        color = type_colors.get(asset, "white")
        flag = r.get("flag", "")
        table.add_row(
            str(i),
            f"[{color}]{r['symbol']}[/{color}]",
            r.get("name", "")[:40],
            r.get("exchange_display", r.get("exchange", "")),
            f"[{color}]{asset}[/{color}]",
            r.get("currency", ""),
            flag,
        )

    console.print(table)


def display_global_overview(quotes: Dict[str, RealTimeQuote]):
    """Full global market overview with all regions."""
    console.print(Rule("[bold cyan]Global Market Overview[/bold cyan]", style="cyan"))

    for region, index_names in INDICES_BY_REGION.items():
        table = Table(
            title=region, box=box.SIMPLE, show_header=True,
            header_style="dim", border_style="dim", padding=(0, 1),
        )
        table.add_column("Index", min_width=18, no_wrap=True)
        table.add_column("Price", justify="right", min_width=14)
        table.add_column("Change%", justify="right", min_width=9)
        table.add_column("Status", justify="center", min_width=9)

        for name in index_names:
            sym = MAJOR_INDICES.get(name)
            if not sym:
                continue
            q = quotes.get(sym)
            if not q or q.price is None:
                table.add_row(name, "[dim]—[/dim]", "[dim]—[/dim]", "[dim]N/A[/dim]")
                continue

            table.add_row(
                f"[dim]{name}[/dim]",
                _fmt_price(q),
                _pct_markup(q.change_pct),
                _status_badge(q.market_status),
            )

        console.print(table)

    console.print(build_market_status_panel())


def display_intraday_analysis(analysis: Dict):
    """Display intraday analysis results."""
    if "error" in analysis:
        console.print(f"[red]{analysis['error']}[/red]")
        return

    symbol = analysis["symbol"]
    interval = analysis["interval"]
    date = analysis["date"]

    console.print(Rule(f"[bold cyan]Intraday Analysis: {symbol} ({interval}) — {date}[/bold cyan]", style="cyan"))

    # Session summary
    chg = analysis.get("session_change_pct")
    chg_color = "green" if (chg or 0) >= 0 else "red"

    session_table = Table.grid(padding=(0, 3))
    session_table.add_column(style="dim")
    session_table.add_column()
    session_table.add_column(style="dim")
    session_table.add_column()
    session_table.add_column(style="dim")
    session_table.add_column()

    levels = analysis.get("levels", {})
    sym_str = get_currency_symbol("USD")  # approximation

    session_table.add_row(
        "Open:", f"${analysis.get('session_open', 0):.2f}" if analysis.get('session_open') else "—",
        "High:", f"[green]${analysis.get('session_high', 0):.2f}[/green]" if analysis.get('session_high') else "—",
        "Low:", f"[red]${analysis.get('session_low', 0):.2f}[/red]" if analysis.get('session_low') else "—",
    )
    session_table.add_row(
        "Session Chg:", f"[{chg_color}]{(chg or 0):+.2f}%[/{chg_color}]",
        "Volume:", _fmt_vol(analysis.get("session_volume")),
        "Bars:", str(analysis.get("session_bars", "—")),
    )
    session_table.add_row(
        "VWAP:", f"${analysis.get('vwap', 0):.2f}" if analysis.get('vwap') else "—",
        "OR High:", f"${levels.get('or_high', 0):.2f}" if levels.get('or_high') else "—",
        "OR Low:", f"${levels.get('or_low', 0):.2f}" if levels.get('or_low') else "—",
    )
    session_table.add_row(
        "Pivot:", f"${levels.get('pivot', 0):.2f}" if levels.get('pivot') else "—",
        "R1:", f"[red]${levels.get('r1', 0):.2f}[/red]" if levels.get('r1') else "—",
        "S1:", f"[green]${levels.get('s1', 0):.2f}[/green]" if levels.get('s1') else "—",
    )
    gap_pct = levels.get("gap_pct")
    if gap_pct is not None:
        gap_color = "green" if gap_pct > 0 else "red"
        session_table.add_row(
            "Gap:", f"[{gap_color}]{gap_pct:+.2f}%[/{gap_color}]",
            "Prev Close:", f"${levels.get('prev_close', 0):.2f}" if levels.get('prev_close') else "—",
            "", "",
        )

    console.print(Panel(session_table, title="Session Statistics", border_style="cyan"))

    # Intraday indicators
    intra_ind = analysis.get("intraday_indicators", {})
    if intra_ind:
        ind_row = []
        rsi_val = intra_ind.get("rsi")
        if rsi_val:
            rsi_color = "green" if rsi_val < 30 else "red" if rsi_val > 70 else "white"
            ind_row.append(f"RSI: [{rsi_color}]{rsi_val:.1f}[/{rsi_color}]")
        macd_h = intra_ind.get("macd_hist")
        if macd_h is not None:
            macd_color = "green" if macd_h > 0 else "red"
            ind_row.append(f"MACD Hist: [{macd_color}]{macd_h:+.4f}[/{macd_color}]")
        atr_pct = intra_ind.get("atr_pct")
        if atr_pct:
            ind_row.append(f"ATR: {atr_pct:.2f}%")
        console.print("  ".join(ind_row))

    # Volume Profile
    vp = analysis.get("volume_profile")
    poc = analysis.get("poc")
    va_high = analysis.get("va_high")
    va_low = analysis.get("va_low")
    if vp is not None and not vp.empty:
        console.print()
        console.print(Rule("[dim]Volume Profile[/dim]", style="dim"))
        if poc:
            console.print(f"[bold]POC (Point of Control): ${poc:.2f}[/bold]  "
                          f"[dim]Value Area: ${va_low:.2f} – ${va_high:.2f}[/dim]" if va_high else "")
        vp_table = Table(box=box.SIMPLE, show_header=True, header_style="dim", border_style="dim")
        vp_table.add_column("Price Range", min_width=18)
        vp_table.add_column("Volume Bar", min_width=25)
        vp_table.add_column("Vol%", justify="right")
        vp_table.add_column("")

        top_rows = vp.head(15)
        max_vol = top_rows["volume"].max()
        for _, row in top_rows.iterrows():
            bar_len = int((row["volume"] / max_vol) * 20) if max_vol > 0 else 0
            bar = "█" * bar_len + "░" * (20 - bar_len)
            flags = ""
            if row.get("is_poc"):
                flags = "[bold yellow]◄ POC[/bold yellow]"
            elif row.get("is_va"):
                flags = "[dim]VA[/dim]"
            bar_color = "yellow" if row.get("is_poc") else "cyan" if row.get("is_va") else "dim"
            vp_table.add_row(
                f"${row['price_low']:.2f}–${row['price_high']:.2f}",
                f"[{bar_color}]{bar}[/{bar_color}]",
                f"{row['pct_of_total']:.1f}%",
                flags,
            )
        console.print(vp_table)

    # Patterns
    patterns = analysis.get("patterns", [])
    if patterns:
        console.print()
        console.print(Rule("[dim]Intraday Patterns & Signals[/dim]", style="dim"))
        for p in patterns:
            d = p.get("direction", "neutral")
            color = "green" if d == "bullish" else "red" if d == "bearish" else "yellow"
            console.print(f"  [{color}]◆[/{color}] [bold]{p['name']}[/bold]  [dim]{p.get('description', '')}[/dim]")
