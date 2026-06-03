"""
HTML report generator: comprehensive stock analysis report.
"""
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import REPORTS_DIR


def _fmt(val, fmt=".2f", suffix="", prefix="", na="N/A"):
    if val is None:
        return na
    try:
        return f"{prefix}{val:{fmt}}{suffix}"
    except Exception:
        return str(val)


def _color_val(val, good_thresh=0, bad_thresh=None, pct=False, reverse=False):
    if val is None:
        return "<span style='color:#888'>N/A</span>"
    fmt = f"{val:.2f}{'%' if pct else ''}"
    if reverse:
        color = "#66bb6a" if val < good_thresh else "#ef5350"
    else:
        color = "#66bb6a" if val > good_thresh else "#ef5350"
    if bad_thresh is not None:
        if reverse:
            color = "#ef5350" if val > bad_thresh else ("#ffa726" if val > good_thresh else "#66bb6a")
        else:
            color = "#ef5350" if val < bad_thresh else ("#ffa726" if val < good_thresh else "#66bb6a")
    return f"<span style='color:{color}'>{fmt}</span>"


def generate_html_report(
    symbol: str,
    info: Dict,
    ratios: Dict,
    scores: Dict,
    dcf: Dict,
    risk: Dict,
    signals_result: Dict,
    predictions: Dict,
    patterns: List,
    candlestick_pattern: List,
    news_analysis: Dict,
    regime: Dict,
    output_path: Optional[Path] = None,
) -> Path:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    name = info.get("longName", symbol)
    sector = info.get("sector", "N/A")
    price = info.get("currentPrice") or info.get("regularMarketPrice", 0) or 0
    rec = signals_result.get("recommendation", "HOLD")
    composite = signals_result.get("composite", 0)
    grade = scores.get("overall_grade", "N/A")

    rec_colors = {
        "STRONG BUY": "#00e676", "BUY": "#66bb6a",
        "HOLD": "#ffa726", "SELL": "#ef5350", "STRONG SELL": "#b71c1c"
    }
    rec_color = rec_colors.get(rec, "#ffa726")

    # News table
    news_rows = ""
    for art in news_analysis.get("articles", [])[:8]:
        s = art.get("score", 0)
        s_color = "#66bb6a" if s > 0.1 else "#ef5350" if s < -0.1 else "#888"
        news_rows += f"""
        <tr>
            <td style='max-width:400px'>{art.get('title', 'N/A')}</td>
            <td>{art.get('publisher', 'N/A')}</td>
            <td>{art.get('published', 'N/A')}</td>
            <td style='color:{s_color}'>{art.get('sentiment', 'Neutral')}</td>
        </tr>"""

    # ML predictions
    ml_rows = ""
    for horizon, pred in sorted(predictions.items()):
        if "error" in pred:
            ml_rows += f"<tr><td>{horizon}d</td><td colspan='5' style='color:#ef5350'>Error: {pred['error'][:50]}</td></tr>"
            continue
        ret = pred.get("upside", 0)
        ret_color = "#66bb6a" if ret > 0 else "#ef5350"
        ml_rows += f"""<tr>
            <td>{horizon} days</td>
            <td>${pred.get('current_price', 0):.2f}</td>
            <td><strong>${pred.get('predicted_price', 0):.2f}</strong></td>
            <td style='color:{ret_color}'>{ret:+.2f}%</td>
            <td>{pred.get('direction', '?')}</td>
            <td>{pred.get('confidence', 0):.0f}%</td>
        </tr>"""

    # Pattern list
    pattern_html = ""
    for p in (patterns + candlestick_pattern)[:10]:
        d = p.get("direction", "neutral")
        d_color = "#66bb6a" if d == "bullish" else "#ef5350" if d == "bearish" else "#ffa726"
        conf = p.get("confidence", None)
        conf_str = f" ({conf*100:.0f}% conf)" if conf else ""
        pattern_html += f"<li style='color:{d_color}'><strong>{p.get('name')}</strong>{conf_str} — {p.get('description', '')}</li>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Stock Analysis: {symbol}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0d1117; color: #c9d1d9; line-height: 1.6; }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
  .header {{ text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #1e3a5f, #0d1117); border-radius: 12px; margin-bottom: 24px; border: 1px solid #30363d; }}
  .header h1 {{ font-size: 2.5em; color: #58a6ff; }}
  .header .subtitle {{ color: #8b949e; margin-top: 8px; font-size: 1.1em; }}
  .badge {{ display: inline-block; padding: 8px 20px; border-radius: 20px; font-weight: bold; font-size: 1.2em; margin: 10px 4px; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
  .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
  .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 20px; }}
  .card h2 {{ color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 10px; margin-bottom: 16px; font-size: 1.2em; }}
  .card h3 {{ color: #79c0ff; margin: 12px 0 6px; font-size: 1em; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
  th {{ background: #21262d; color: #8b949e; padding: 8px 12px; text-align: left; font-weight: 500; }}
  td {{ padding: 7px 12px; border-bottom: 1px solid #21262d; }}
  tr:hover td {{ background: #1c2128; }}
  .metric {{ display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #21262d; }}
  .metric:last-child {{ border-bottom: none; }}
  .metric .label {{ color: #8b949e; font-size: 0.9em; }}
  .metric .value {{ font-weight: 600; }}
  .regime-badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; background: #21262d; }}
  ul {{ list-style: none; padding: 0; }}
  li {{ padding: 5px 0; border-bottom: 1px solid #21262d; font-size: 0.9em; }}
  .footer {{ text-align: center; margin-top: 40px; color: #484f58; font-size: 0.8em; }}
  @media (max-width: 768px) {{ .grid-2, .grid-3 {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>{symbol}</h1>
  <div class="subtitle">{name} · {sector} · Generated {now}</div>
  <div>
    <span class="badge" style="background:{rec_color}22; color:{rec_color}; border:2px solid {rec_color}">{rec}</span>
    <span class="badge" style="background:#21262d; color:#c9d1d9">Score: {composite:+.3f}</span>
    <span class="badge" style="background:#21262d; color:#f0e68c">Fundamental Grade: {grade}</span>
    <span class="badge" style="background:#21262d; color:#79c0ff">Price: ${price:,.2f}</span>
  </div>
  <div style="margin-top:10px; color:#8b949e">
    Market Regime: <strong style="color:#ffa726">{regime.get('regime', 'Unknown')}</strong> &nbsp;|&nbsp;
    Annualized Volatility: <strong>{regime.get('volatility_annualized', 0):.1f}%</strong>
  </div>
</div>

<div class="grid-3">
  <!-- Valuation -->
  <div class="card">
    <h2>📊 Valuation</h2>
    {"".join(f"<div class='metric'><span class='label'>{k}</span><span class='value'>{_fmt(v)}</span></div>" for k, v in [
      ("P/E (TTM)", ratios.get("pe_ratio")), ("P/E (Fwd)", ratios.get("forward_pe")),
      ("PEG Ratio", ratios.get("peg_ratio")), ("P/B", ratios.get("price_to_book")),
      ("P/S", ratios.get("price_to_sales")), ("EV/EBITDA", ratios.get("ev_ebitda")),
      ("Market Cap", ratios.get("market_cap")), ("EPS (TTM)", ratios.get("eps_trailing")),
    ])}
  </div>

  <!-- Financial Health -->
  <div class="card">
    <h2>💹 Financial Health</h2>
    {"".join(f"<div class='metric'><span class='label'>{k}</span><span class='value'>{v}</span></div>" for k, v in [
      ("ROE", _color_val(ratios.get("return_on_equity", 0) * 100 if ratios.get("return_on_equity") else None, 15, 0, True)),
      ("ROA", _color_val(ratios.get("return_on_assets", 0) * 100 if ratios.get("return_on_assets") else None, 5, 0, True)),
      ("Net Margin", _color_val(ratios.get("profit_margins", 0) * 100 if ratios.get("profit_margins") else None, 10, 0, True)),
      ("Revenue Growth", _color_val(ratios.get("revenue_growth", 0) * 100 if ratios.get("revenue_growth") else None, 5, 0, True)),
      ("D/E Ratio", _color_val(ratios.get("debt_to_equity"), 0, 150, False, True)),
      ("Current Ratio", _color_val(ratios.get("current_ratio"), 1.5, 1.0)),
      ("Dividend Yield", f"{ratios.get('dividend_yield', 0) * 100:.2f}%" if ratios.get("dividend_yield") else "N/A"),
      ("Beta", _fmt(ratios.get("beta"))),
    ])}
  </div>

  <!-- DCF Valuation -->
  <div class="card">
    <h2>🎯 DCF & Analyst Targets</h2>
    {"".join(f"<div class='metric'><span class='label'>{k}</span><span class='value'>{v}</span></div>" for k, v in [
      ("Current Price", f"${price:,.2f}"),
      ("DCF Intrinsic Value", f"${dcf.get('intrinsic_value', 0):.2f}" if dcf.get('intrinsic_value') else "N/A"),
      ("DCF Upside", _color_val(dcf.get("upside"), 10, -10, True) if dcf.get("upside") is not None else "N/A"),
      ("Margin of Safety", _color_val(dcf.get("margin_of_safety"), 20, -10, True) if dcf.get("margin_of_safety") is not None else "N/A"),
      ("Analyst Target", f"${ratios.get('analyst_target', 0):.2f}" if ratios.get("analyst_target") else "N/A"),
      ("Analyst Range", f"${ratios.get('analyst_low', 0):.2f} – ${ratios.get('analyst_high', 0):.2f}" if ratios.get("analyst_low") else "N/A"),
      ("Recommendation", ratios.get("recommendation", "N/A").title() if ratios.get("recommendation") else "N/A"),
      ("52W High/Low", f"${ratios.get('52w_high', 0):.2f} / ${ratios.get('52w_low', 0):.2f}" if ratios.get("52w_high") else "N/A"),
    ])}
  </div>
</div>

<div class="grid-2">
  <!-- Risk Metrics -->
  <div class="card">
    <h2>⚠️ Risk Metrics</h2>
    {"".join(f"<div class='metric'><span class='label'>{k}</span><span class='value'>{v}</span></div>" for k, v in [
      ("Annual Return", _color_val(risk.get("annual_return"), 0, -10, True)),
      ("Annual Volatility", _fmt(risk.get("volatility_annual")) + "%"),
      ("Max Drawdown", _color_val(risk.get("max_drawdown"), -10, -30, True, reverse=True)),
      ("Sharpe Ratio", _color_val(risk.get("sharpe_ratio"), 1.0, 0.5)),
      ("Sortino Ratio", _color_val(risk.get("sortino_ratio"), 1.5, 0.5)),
      ("Calmar Ratio", _color_val(risk.get("calmar_ratio"), 1.0, 0.3) if risk.get("calmar_ratio") else "N/A"),
      ("VaR 95% (daily)", f"{risk.get('var_95_historical', 0):.3f}%"),
      ("CVaR 95% (daily)", f"{risk.get('cvar_95', 0):.3f}%"),
      ("Win Rate", f"{risk.get('win_rate', 0):.1f}%"),
      ("Profit Factor", _fmt(risk.get("profit_factor"))),
      ("Skewness", _fmt(risk.get("skewness"), ".3f")),
      ("Kurtosis", _fmt(risk.get("kurtosis"), ".3f")),
    ])}
  </div>

  <!-- Technical Signals -->
  <div class="card">
    <h2>📈 Technical Signals</h2>
    <div class="metric">
      <span class="label">Composite Signal</span>
      <span class="value" style="color:{rec_color}">{rec} ({composite:+.3f})</span>
    </div>
    <div class="metric">
      <span class="label">Trend Score</span>
      <span class="value">{signals_result.get('category_scores', {}).get('trend', 0):+.2f}</span>
    </div>
    <div class="metric">
      <span class="label">Momentum Score</span>
      <span class="value">{signals_result.get('category_scores', {}).get('momentum', 0):+.2f}</span>
    </div>
    <div class="metric">
      <span class="label">Volume Score</span>
      <span class="value">{signals_result.get('category_scores', {}).get('volume', 0):+.2f}</span>
    </div>
    <div class="metric">
      <span class="label">Volatility Score</span>
      <span class="value">{signals_result.get('category_scores', {}).get('volatility', 0):+.2f}</span>
    </div>
    <h3>Detected Patterns</h3>
    <ul>{pattern_html or "<li style='color:#888'>No significant patterns detected</li>"}</ul>
  </div>
</div>

<!-- ML Predictions -->
<div class="card" style="margin-bottom:20px">
  <h2>🤖 ML Price Predictions (Ensemble: RF + GBM + Ridge)</h2>
  <table>
    <tr><th>Horizon</th><th>Current Price</th><th>Predicted Price</th><th>Expected Return</th><th>Direction</th><th>Confidence</th></tr>
    {ml_rows or "<tr><td colspan='6' style='color:#888'>ML predictions not available</td></tr>"}
  </table>
  <p style="color:#484f58; font-size:0.8em; margin-top:8px">⚠️ ML predictions are probabilistic estimates based on historical patterns, not financial advice.</p>
</div>

<!-- News Sentiment -->
<div class="card" style="margin-bottom:20px">
  <h2>📰 News Sentiment Analysis</h2>
  <div style="margin-bottom:12px">
    <strong>Overall Sentiment:</strong> {news_analysis.get('overall_sentiment', 'N/A')} &nbsp;
    (Score: {news_analysis.get('overall_score', 0):.3f}) &nbsp;|&nbsp;
    Positive: {news_analysis.get('positive_count', 0)} &nbsp;
    Negative: {news_analysis.get('negative_count', 0)} &nbsp;
    Neutral: {news_analysis.get('neutral_count', 0)}
  </div>
  <table>
    <tr><th>Headline</th><th>Publisher</th><th>Published</th><th>Sentiment</th></tr>
    {news_rows or "<tr><td colspan='4' style='color:#888'>No recent news available</td></tr>"}
  </table>
</div>

<div class="footer">
  <p>Generated by Advanced Stock Analyzer | {now}</p>
  <p>⚠️ This report is for educational purposes only and does not constitute financial advice.</p>
</div>

</div>
</body>
</html>"""

    path = output_path or REPORTS_DIR / f"{symbol}_report.html"
    path.write_text(html, encoding="utf-8")
    return path
