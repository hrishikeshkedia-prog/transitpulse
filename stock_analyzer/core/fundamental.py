"""
Fundamental analysis module: ratios, DCF valuation, peer comparison.
"""
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd


def _safe(val, default=None):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return default
    return val


def extract_ratios(info: Dict) -> Dict[str, Any]:
    """Extract key fundamental ratios from yfinance info dict."""
    return {
        # Valuation
        "market_cap": _safe(info.get("marketCap")),
        "enterprise_value": _safe(info.get("enterpriseValue")),
        "pe_ratio": _safe(info.get("trailingPE")),
        "forward_pe": _safe(info.get("forwardPE")),
        "peg_ratio": _safe(info.get("pegRatio")),
        "price_to_book": _safe(info.get("priceToBook")),
        "price_to_sales": _safe(info.get("priceToSalesTrailing12Months")),
        "ev_ebitda": _safe(info.get("enterpriseToEbitda")),
        "ev_revenue": _safe(info.get("enterpriseToRevenue")),
        # Profitability
        "gross_margins": _safe(info.get("grossMargins")),
        "operating_margins": _safe(info.get("operatingMargins")),
        "profit_margins": _safe(info.get("profitMargins")),
        "return_on_equity": _safe(info.get("returnOnEquity")),
        "return_on_assets": _safe(info.get("returnOnAssets")),
        "ebitda_margins": _safe(info.get("ebitdaMargins")),
        # Growth
        "revenue_growth": _safe(info.get("revenueGrowth")),
        "earnings_growth": _safe(info.get("earningsGrowth")),
        "earnings_quarterly_growth": _safe(info.get("earningsQuarterlyGrowth")),
        # Dividends
        "dividend_yield": _safe(info.get("dividendYield")),
        "dividend_rate": _safe(info.get("dividendRate")),
        "payout_ratio": _safe(info.get("payoutRatio")),
        "five_year_avg_dividend_yield": _safe(info.get("fiveYearAvgDividendYield")),
        # Balance Sheet
        "total_debt": _safe(info.get("totalDebt")),
        "total_cash": _safe(info.get("totalCash")),
        "debt_to_equity": _safe(info.get("debtToEquity")),
        "current_ratio": _safe(info.get("currentRatio")),
        "quick_ratio": _safe(info.get("quickRatio")),
        "book_value_per_share": _safe(info.get("bookValue")),
        # Cash Flow
        "free_cash_flow": _safe(info.get("freeCashflow")),
        "operating_cash_flow": _safe(info.get("operatingCashflow")),
        "total_revenue": _safe(info.get("totalRevenue")),
        "ebitda": _safe(info.get("ebitda")),
        "net_income": _safe(info.get("netIncomeToCommon")),
        "eps_trailing": _safe(info.get("trailingEps")),
        "eps_forward": _safe(info.get("forwardEps")),
        # Per share
        "revenue_per_share": _safe(info.get("revenuePerShare")),
        # Float / ownership
        "shares_outstanding": _safe(info.get("sharesOutstanding")),
        "float_shares": _safe(info.get("floatShares")),
        "short_ratio": _safe(info.get("shortRatio")),
        "short_percent_float": _safe(info.get("shortPercentOfFloat")),
        "institutional_holdings": _safe(info.get("heldPercentInstitutions")),
        "insider_holdings": _safe(info.get("heldPercentInsiders")),
        # Beta & 52w
        "beta": _safe(info.get("beta")),
        "52w_high": _safe(info.get("fiftyTwoWeekHigh")),
        "52w_low": _safe(info.get("fiftyTwoWeekLow")),
        "52w_change": _safe(info.get("52WeekChange")),
        "50d_avg": _safe(info.get("fiftyDayAverage")),
        "200d_avg": _safe(info.get("twoHundredDayAverage")),
        "analyst_target": _safe(info.get("targetMeanPrice")),
        "analyst_low": _safe(info.get("targetLowPrice")),
        "analyst_high": _safe(info.get("targetHighPrice")),
        "recommendation": _safe(info.get("recommendationKey")),
    }


def dcf_valuation(
    info: Dict,
    growth_rate: Optional[float] = None,
    terminal_growth: float = 0.025,
    discount_rate: float = 0.10,
    years: int = 10,
) -> Dict[str, float]:
    """
    Discounted Cash Flow valuation.
    Uses free cash flow as the base; falls back to operating cash flow.
    """
    fcf = _safe(info.get("freeCashflow"))
    if fcf is None:
        fcf = _safe(info.get("operatingCashflow"))
    shares = _safe(info.get("sharesOutstanding"))

    if fcf is None or shares is None or shares == 0:
        return {}

    # Determine growth rate
    if growth_rate is None:
        eg = _safe(info.get("earningsGrowth"), 0.08)
        rg = _safe(info.get("revenueGrowth"), 0.06)
        growth_rate = min(max((eg + rg) / 2, 0.02), 0.30)

    # Stage 1: explicit forecast (years 1–10 with declining growth)
    cash_flows = []
    cf = fcf
    for y in range(1, years + 1):
        decay = 1 - (y - 1) / (years * 2)
        g = growth_rate * max(decay, 0.3)
        cf = cf * (1 + g)
        pv = cf / (1 + discount_rate) ** y
        cash_flows.append(pv)

    # Stage 2: Terminal Value (Gordon Growth)
    terminal_cf = cash_flows[-1] * (1 + discount_rate) ** years * (1 + terminal_growth)
    terminal_value = terminal_cf / (discount_rate - terminal_growth)
    pv_terminal = terminal_value / (1 + discount_rate) ** years

    total_pv = sum(cash_flows) + pv_terminal
    intrinsic_value_per_share = total_pv / shares

    current_price = _safe(info.get("currentPrice"), _safe(info.get("regularMarketPrice"), 0))
    margin_of_safety = (intrinsic_value_per_share - current_price) / intrinsic_value_per_share if intrinsic_value_per_share > 0 else None

    return {
        "intrinsic_value": intrinsic_value_per_share,
        "current_price": current_price,
        "upside": ((intrinsic_value_per_share / current_price) - 1) * 100 if current_price and current_price > 0 else None,
        "margin_of_safety": margin_of_safety * 100 if margin_of_safety else None,
        "pv_cash_flows": sum(cash_flows),
        "pv_terminal": pv_terminal,
        "growth_rate_used": growth_rate,
        "discount_rate": discount_rate,
    }


def graham_number(info: Dict) -> Optional[float]:
    """Graham Number: sqrt(22.5 * EPS * BVPS)."""
    eps = _safe(info.get("trailingEps"))
    bvps = _safe(info.get("bookValue"))
    if eps and bvps and eps > 0 and bvps > 0:
        return np.sqrt(22.5 * eps * bvps)
    return None


def lynch_fair_value(info: Dict) -> Optional[float]:
    """Peter Lynch Fair Value: PEG × EPS × 100."""
    eps = _safe(info.get("trailingEps"))
    growth = _safe(info.get("earningsGrowth"))
    if eps and growth and eps > 0 and growth > 0:
        return eps * growth * 100 * 100
    return None


def score_fundamentals(ratios: Dict) -> Dict[str, Any]:
    """Score each fundamental metric and compute an overall grade."""
    scores = {}

    def score_metric(val, thresholds, labels, reverse=False):
        if val is None:
            return None
        if reverse:
            thresholds = thresholds[::-1]
            labels = labels[::-1]
        for threshold, label in zip(thresholds, labels):
            if val <= threshold:
                return label
        return labels[-1]

    # P/E score (lower is better for value)
    pe = ratios.get("pe_ratio")
    if pe and pe > 0:
        if pe < 10:
            scores["pe_score"] = ("Excellent", 5)
        elif pe < 15:
            scores["pe_score"] = ("Good", 4)
        elif pe < 25:
            scores["pe_score"] = ("Fair", 3)
        elif pe < 40:
            scores["pe_score"] = ("Expensive", 2)
        else:
            scores["pe_score"] = ("Very Expensive", 1)

    # PEG score
    peg = ratios.get("peg_ratio")
    if peg and peg > 0:
        if peg < 0.5:
            scores["peg_score"] = ("Severely Undervalued", 5)
        elif peg < 1.0:
            scores["peg_score"] = ("Undervalued", 4)
        elif peg < 1.5:
            scores["peg_score"] = ("Fair Value", 3)
        elif peg < 2.5:
            scores["peg_score"] = ("Overvalued", 2)
        else:
            scores["peg_score"] = ("Highly Overvalued", 1)

    # ROE
    roe = ratios.get("return_on_equity")
    if roe is not None:
        roe_pct = roe * 100
        if roe_pct > 20:
            scores["roe_score"] = ("Excellent", 5)
        elif roe_pct > 15:
            scores["roe_score"] = ("Good", 4)
        elif roe_pct > 10:
            scores["roe_score"] = ("Average", 3)
        elif roe_pct > 0:
            scores["roe_score"] = ("Below Average", 2)
        else:
            scores["roe_score"] = ("Negative", 1)

    # Profit margin
    margin = ratios.get("profit_margins")
    if margin is not None:
        m_pct = margin * 100
        if m_pct > 20:
            scores["margin_score"] = ("Excellent", 5)
        elif m_pct > 10:
            scores["margin_score"] = ("Good", 4)
        elif m_pct > 5:
            scores["margin_score"] = ("Average", 3)
        elif m_pct > 0:
            scores["margin_score"] = ("Thin", 2)
        else:
            scores["margin_score"] = ("Unprofitable", 1)

    # D/E ratio (lower is safer)
    de = ratios.get("debt_to_equity")
    if de is not None:
        if de < 30:
            scores["de_score"] = ("Very Low Debt", 5)
        elif de < 60:
            scores["de_score"] = ("Low Debt", 4)
        elif de < 100:
            scores["de_score"] = ("Moderate Debt", 3)
        elif de < 200:
            scores["de_score"] = ("High Debt", 2)
        else:
            scores["de_score"] = ("Very High Debt", 1)

    # Revenue growth
    rg = ratios.get("revenue_growth")
    if rg is not None:
        rg_pct = rg * 100
        if rg_pct > 20:
            scores["growth_score"] = ("High Growth", 5)
        elif rg_pct > 10:
            scores["growth_score"] = ("Good Growth", 4)
        elif rg_pct > 0:
            scores["growth_score"] = ("Positive", 3)
        elif rg_pct > -10:
            scores["growth_score"] = ("Declining", 2)
        else:
            scores["growth_score"] = ("Contracting", 1)

    # Current ratio (liquidity)
    cr = ratios.get("current_ratio")
    if cr is not None:
        if cr > 2:
            scores["liquidity_score"] = ("Excellent", 5)
        elif cr > 1.5:
            scores["liquidity_score"] = ("Good", 4)
        elif cr > 1.0:
            scores["liquidity_score"] = ("Adequate", 3)
        elif cr > 0.5:
            scores["liquidity_score"] = ("Weak", 2)
        else:
            scores["liquidity_score"] = ("Critical", 1)

    # Composite score
    numeric_scores = [v[1] for v in scores.values() if isinstance(v, tuple)]
    if numeric_scores:
        avg = np.mean(numeric_scores)
        if avg >= 4.5:
            grade = "A+"
        elif avg >= 4.0:
            grade = "A"
        elif avg >= 3.5:
            grade = "B+"
        elif avg >= 3.0:
            grade = "B"
        elif avg >= 2.5:
            grade = "C+"
        elif avg >= 2.0:
            grade = "C"
        else:
            grade = "D"
        scores["overall_grade"] = grade
        scores["overall_score"] = avg

    return scores


def analyze_financials(financials: Dict) -> Dict:
    """Extract trends from financial statements."""
    result = {}
    income = financials.get("income_stmt")
    balance = financials.get("balance_sheet")
    cashflow = financials.get("cash_flow")

    def get_row(df, *keys):
        if df is None or df.empty:
            return None
        for key in keys:
            for idx in df.index:
                if key.lower() in str(idx).lower():
                    return df.loc[idx]
        return None

    def yoy_growth(series):
        if series is None or len(series) < 2:
            return None
        vals = series.dropna()
        if len(vals) < 2:
            return None
        return float((vals.iloc[0] - vals.iloc[1]) / abs(vals.iloc[1])) * 100 if vals.iloc[1] != 0 else None

    # Income statement
    revenue = get_row(income, "Total Revenue", "Revenue")
    if revenue is not None:
        result["revenue_trend"] = revenue.dropna().tolist()[:4]
        result["revenue_yoy"] = yoy_growth(revenue)

    net_income = get_row(income, "Net Income")
    if net_income is not None:
        result["net_income_trend"] = net_income.dropna().tolist()[:4]
        result["net_income_yoy"] = yoy_growth(net_income)

    ebitda = get_row(income, "EBITDA")
    if ebitda is not None:
        result["ebitda_trend"] = ebitda.dropna().tolist()[:4]

    # Balance sheet
    total_debt = get_row(balance, "Total Debt", "Long Term Debt")
    cash = get_row(balance, "Cash And Cash Equivalents", "Cash")
    if total_debt is not None and cash is not None:
        d = total_debt.dropna()
        c = cash.dropna()
        if len(d) and len(c):
            result["net_debt"] = float(d.iloc[0] - c.iloc[0])

    # Cash flow
    fcf_row = get_row(cashflow, "Free Cash Flow")
    if fcf_row is not None:
        result["fcf_trend"] = fcf_row.dropna().tolist()[:4]
        result["fcf_yoy"] = yoy_growth(fcf_row)

    capex = get_row(cashflow, "Capital Expenditure", "Capex")
    if capex is not None:
        result["capex_trend"] = capex.dropna().tolist()[:4]

    return result
