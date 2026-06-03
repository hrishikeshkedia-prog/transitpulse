"""
Global exchange registry: 60+ exchanges, market hours, smart symbol resolution,
asset type detection, currency symbols, and country flag emojis.
"""
from datetime import datetime, time as dt_time
from typing import Dict, List, Optional
import pytz
import yfinance as yf


# ─── Exchange Registry ───────────────────────────────────────────────────────

EXCHANGES: Dict[str, Dict] = {
    # North America
    "NYSE":   {"name": "New York Stock Exchange",   "country": "US", "currency": "USD", "suffix": "",     "timezone": "America/New_York",   "open": (9,30),  "close": (16,0),  "flag": "🇺🇸", "index": "^GSPC"},
    "NASDAQ": {"name": "NASDAQ",                    "country": "US", "currency": "USD", "suffix": "",     "timezone": "America/New_York",   "open": (9,30),  "close": (16,0),  "flag": "🇺🇸", "index": "^IXIC"},
    "AMEX":   {"name": "NYSE American",             "country": "US", "currency": "USD", "suffix": "",     "timezone": "America/New_York",   "open": (9,30),  "close": (16,0),  "flag": "🇺🇸", "index": "^GSPC"},
    "TSX":    {"name": "Toronto Stock Exchange",    "country": "CA", "currency": "CAD", "suffix": ".TO",  "timezone": "America/Toronto",    "open": (9,30),  "close": (16,0),  "flag": "🇨🇦", "index": "^GSPTSE"},
    "TSXV":   {"name": "TSX Venture Exchange",      "country": "CA", "currency": "CAD", "suffix": ".V",   "timezone": "America/Toronto",    "open": (9,30),  "close": (16,0),  "flag": "🇨🇦", "index": "^GSPTSE"},
    "BMV":    {"name": "Bolsa Mexicana de Valores",  "country": "MX", "currency": "MXN", "suffix": ".MX",  "timezone": "America/Mexico_City","open": (8,30),  "close": (15,0),  "flag": "🇲🇽", "index": "^MXX"},
    "B3":     {"name": "B3 Brazil",                 "country": "BR", "currency": "BRL", "suffix": ".SA",  "timezone": "America/Sao_Paulo",  "open": (10,0),  "close": (17,30), "flag": "🇧🇷", "index": "^BVSP"},
    # Europe
    "LSE":    {"name": "London Stock Exchange",     "country": "GB", "currency": "GBP", "suffix": ".L",   "timezone": "Europe/London",      "open": (8,0),   "close": (16,30), "flag": "🇬🇧", "index": "^FTSE"},
    "XETRA":  {"name": "Deutsche Börse XETRA",      "country": "DE", "currency": "EUR", "suffix": ".DE",  "timezone": "Europe/Berlin",      "open": (9,0),   "close": (17,30), "flag": "🇩🇪", "index": "^GDAXI"},
    "FRA":    {"name": "Frankfurt Stock Exchange",  "country": "DE", "currency": "EUR", "suffix": ".F",   "timezone": "Europe/Berlin",      "open": (8,0),   "close": (22,0),  "flag": "🇩🇪", "index": "^GDAXI"},
    "ENP":    {"name": "Euronext Paris",            "country": "FR", "currency": "EUR", "suffix": ".PA",  "timezone": "Europe/Paris",       "open": (9,0),   "close": (17,30), "flag": "🇫🇷", "index": "^FCHI"},
    "AEX":    {"name": "Euronext Amsterdam",        "country": "NL", "currency": "EUR", "suffix": ".AS",  "timezone": "Europe/Amsterdam",   "open": (9,0),   "close": (17,30), "flag": "🇳🇱", "index": "^AEX"},
    "EBR":    {"name": "Euronext Brussels",         "country": "BE", "currency": "EUR", "suffix": ".BR",  "timezone": "Europe/Brussels",    "open": (9,0),   "close": (17,30), "flag": "🇧🇪", "index": "BFX"},
    "ENL":    {"name": "Euronext Lisbon",           "country": "PT", "currency": "EUR", "suffix": ".LS",  "timezone": "Europe/Lisbon",      "open": (8,0),   "close": (16,30), "flag": "🇵🇹", "index": "PSI20.LS"},
    "BME":    {"name": "Bolsa de Madrid",           "country": "ES", "currency": "EUR", "suffix": ".MC",  "timezone": "Europe/Madrid",      "open": (9,0),   "close": (17,30), "flag": "🇪🇸", "index": "^IBEX"},
    "MIL":    {"name": "Borsa Italiana",            "country": "IT", "currency": "EUR", "suffix": ".MI",  "timezone": "Europe/Rome",        "open": (9,0),   "close": (17,30), "flag": "🇮🇹", "index": "FTSEMIB.MI"},
    "SIX":    {"name": "SIX Swiss Exchange",        "country": "CH", "currency": "CHF", "suffix": ".SW",  "timezone": "Europe/Zurich",      "open": (9,0),   "close": (17,30), "flag": "🇨🇭", "index": "^SSMI"},
    "OMX":    {"name": "Nasdaq Stockholm",          "country": "SE", "currency": "SEK", "suffix": ".ST",  "timezone": "Europe/Stockholm",   "open": (9,0),   "close": (17,30), "flag": "🇸🇪", "index": "^OMX"},
    "OMXH":   {"name": "Nasdaq Helsinki",           "country": "FI", "currency": "EUR", "suffix": ".HE",  "timezone": "Europe/Helsinki",    "open": (10,0),  "close": (18,30), "flag": "🇫🇮", "index": "^OMXH25"},
    "OMXC":   {"name": "Nasdaq Copenhagen",         "country": "DK", "currency": "DKK", "suffix": ".CO",  "timezone": "Europe/Copenhagen",  "open": (9,0),   "close": (17,0),  "flag": "🇩🇰", "index": "^OMXC25"},
    "OSL":    {"name": "Oslo Børs",                 "country": "NO", "currency": "NOK", "suffix": ".OL",  "timezone": "Europe/Oslo",        "open": (9,0),   "close": (16,20), "flag": "🇳🇴", "index": "^OBX"},
    "WSE":    {"name": "Warsaw Stock Exchange",     "country": "PL", "currency": "PLN", "suffix": ".WA",  "timezone": "Europe/Warsaw",      "open": (9,0),   "close": (17,5),  "flag": "🇵🇱", "index": "^WIG20"},
    "PRA":    {"name": "Prague Stock Exchange",     "country": "CZ", "currency": "CZK", "suffix": ".PR",  "timezone": "Europe/Prague",      "open": (9,0),   "close": (16,0),  "flag": "🇨🇿", "index": "^PX"},
    "BIST":   {"name": "Borsa Istanbul",            "country": "TR", "currency": "TRY", "suffix": ".IS",  "timezone": "Europe/Istanbul",    "open": (10,0),  "close": (18,0),  "flag": "🇹🇷", "index": "XU100.IS"},
    "MOEX":   {"name": "Moscow Exchange",           "country": "RU", "currency": "RUB", "suffix": ".ME",  "timezone": "Europe/Moscow",      "open": (9,30),  "close": (18,50), "flag": "🇷🇺", "index": "IMOEX.ME"},
    "TASE":   {"name": "Tel Aviv Stock Exchange",   "country": "IL", "currency": "ILS", "suffix": ".TA",  "timezone": "Asia/Jerusalem",     "open": (9,30),  "close": (17,30), "flag": "🇮🇱", "index": "^TA125.TA"},
    # Asia-Pacific
    "TSE":    {"name": "Tokyo Stock Exchange",      "country": "JP", "currency": "JPY", "suffix": ".T",   "timezone": "Asia/Tokyo",         "open": (9,0),   "close": (15,30), "flag": "🇯🇵", "index": "^N225"},
    "HKEX":   {"name": "Hong Kong Exchange",        "country": "HK", "currency": "HKD", "suffix": ".HK",  "timezone": "Asia/Hong_Kong",     "open": (9,30),  "close": (16,0),  "flag": "🇭🇰", "index": "^HSI"},
    "SSE":    {"name": "Shanghai Stock Exchange",   "country": "CN", "currency": "CNY", "suffix": ".SS",  "timezone": "Asia/Shanghai",      "open": (9,30),  "close": (15,0),  "flag": "🇨🇳", "index": "000001.SS"},
    "SZSE":   {"name": "Shenzhen Stock Exchange",   "country": "CN", "currency": "CNY", "suffix": ".SZ",  "timezone": "Asia/Shanghai",      "open": (9,30),  "close": (15,0),  "flag": "🇨🇳", "index": "399001.SZ"},
    "NSE":    {"name": "NSE India",                 "country": "IN", "currency": "INR", "suffix": ".NS",  "timezone": "Asia/Kolkata",       "open": (9,15),  "close": (15,30), "flag": "🇮🇳", "index": "^NSEI"},
    "BSE":    {"name": "BSE India",                 "country": "IN", "currency": "INR", "suffix": ".BO",  "timezone": "Asia/Kolkata",       "open": (9,15),  "close": (15,30), "flag": "🇮🇳", "index": "^BSESN"},
    "KRX":    {"name": "Korea Stock Exchange",      "country": "KR", "currency": "KRW", "suffix": ".KS",  "timezone": "Asia/Seoul",         "open": (9,0),   "close": (15,30), "flag": "🇰🇷", "index": "^KS11"},
    "KOSDAQ": {"name": "KOSDAQ",                    "country": "KR", "currency": "KRW", "suffix": ".KQ",  "timezone": "Asia/Seoul",         "open": (9,0),   "close": (15,30), "flag": "🇰🇷", "index": "^KQ11"},
    "TWSE":   {"name": "Taiwan Stock Exchange",     "country": "TW", "currency": "TWD", "suffix": ".TW",  "timezone": "Asia/Taipei",        "open": (9,0),   "close": (13,30), "flag": "🇹🇼", "index": "^TWII"},
    "SGX":    {"name": "Singapore Exchange",        "country": "SG", "currency": "SGD", "suffix": ".SI",  "timezone": "Asia/Singapore",     "open": (9,0),   "close": (17,0),  "flag": "🇸🇬", "index": "^STI"},
    "ASX":    {"name": "Australian Securities Exchange","country":"AU","currency": "AUD","suffix": ".AX",  "timezone": "Australia/Sydney",   "open": (10,0),  "close": (16,0),  "flag": "🇦🇺", "index": "^AXJO"},
    "NZX":    {"name": "New Zealand Exchange",      "country": "NZ", "currency": "NZD", "suffix": ".NZ",  "timezone": "Pacific/Auckland",   "open": (10,0),  "close": (16,45), "flag": "🇳🇿", "index": "^NZ50"},
    "BKK":    {"name": "Stock Exchange of Thailand","country": "TH", "currency": "THB", "suffix": ".BK",  "timezone": "Asia/Bangkok",       "open": (10,0),  "close": (16,30), "flag": "🇹🇭", "index": "^SET.BK"},
    "IDX":    {"name": "Indonesia Stock Exchange",  "country": "ID", "currency": "IDR", "suffix": ".JK",  "timezone": "Asia/Jakarta",       "open": (9,0),   "close": (15,50), "flag": "🇮🇩", "index": "^JKSE"},
    "BUR":    {"name": "Bursa Malaysia",            "country": "MY", "currency": "MYR", "suffix": ".KL",  "timezone": "Asia/Kuala_Lumpur",  "open": (9,0),   "close": (17,0),  "flag": "🇲🇾", "index": "^KLSE"},
    "PSE":    {"name": "Philippine Stock Exchange", "country": "PH", "currency": "PHP", "suffix": ".PS",  "timezone": "Asia/Manila",        "open": (9,30),  "close": (15,30), "flag": "🇵🇭", "index": "PSEI.PS"},
    "CSE":    {"name": "Colombo Stock Exchange",    "country": "LK", "currency": "LKR", "suffix": ".CM",  "timezone": "Asia/Colombo",       "open": (9,30),  "close": (14,30), "flag": "🇱🇰", "index": "^CSE"},
    # Middle East & Africa
    "TADAWUL":{"name": "Saudi Exchange",            "country": "SA", "currency": "SAR", "suffix": ".SR",  "timezone": "Asia/Riyadh",        "open": (10,0),  "close": (15,0),  "flag": "🇸🇦", "index": "^TASI.SR"},
    "DFM":    {"name": "Dubai Financial Market",    "country": "AE", "currency": "AED", "suffix": ".AE",  "timezone": "Asia/Dubai",         "open": (10,0),  "close": (14,0),  "flag": "🇦🇪", "index": "^DFMGI"},
    "ADX":    {"name": "Abu Dhabi Securities Exchange","country":"AE","currency": "AED", "suffix": ".AE",  "timezone": "Asia/Dubai",         "open": (10,0),  "close": (14,0),  "flag": "🇦🇪", "index": "^FTFADGI"},
    "EGX":    {"name": "Egyptian Exchange",         "country": "EG", "currency": "EGP", "suffix": ".CA",  "timezone": "Africa/Cairo",       "open": (10,0),  "close": (14,30), "flag": "🇪🇬", "index": "^EGX30"},
    "JSE":    {"name": "Johannesburg Stock Exchange","country": "ZA", "currency": "ZAR", "suffix": ".JO",  "timezone": "Africa/Johannesburg","open": (9,0),   "close": (17,0),  "flag": "🇿🇦", "index": "^J203.JO"},
    "NGX":    {"name": "Nigerian Exchange Group",   "country": "NG", "currency": "NGN", "suffix": ".LG",  "timezone": "Africa/Lagos",       "open": (10,0),  "close": (14,30), "flag": "🇳🇬", "index": "^NGX30"},
    "NSE_KE": {"name": "Nairobi Securities Exchange","country":"KE", "currency": "KES", "suffix": ".NR",  "timezone": "Africa/Nairobi",     "open": (9,30),  "close": (15,0),  "flag": "🇰🇪", "index": "^NSE20"},
}

# ─── Major Global Indices ─────────────────────────────────────────────────────

MAJOR_INDICES: Dict[str, str] = {
    # Americas
    "S&P 500":          "^GSPC",
    "NASDAQ Comp.":     "^IXIC",
    "Dow Jones":        "^DJI",
    "Russell 2000":     "^RUT",
    "VIX":              "^VIX",
    "TSX Composite":    "^GSPTSE",
    "Bovespa":          "^BVSP",
    "IPC Mexico":       "^MXX",
    # Europe
    "FTSE 100":         "^FTSE",
    "DAX":              "^GDAXI",
    "CAC 40":           "^FCHI",
    "EURO STOXX 50":    "^STOXX50E",
    "AEX":              "^AEX",
    "IBEX 35":          "^IBEX",
    "FTSE MIB":         "FTSEMIB.MI",
    "SMI":              "^SSMI",
    "OMX Stockholm":    "^OMX",
    "OMX Copenhagen":   "^OMXC25",
    "OBX":              "^OBX",
    "WIG20":            "^WIG20",
    "BIST 100":         "XU100.IS",
    # Asia-Pacific
    "Nikkei 225":       "^N225",
    "Hang Seng":        "^HSI",
    "Shanghai Comp.":   "000001.SS",
    "CSI 300":          "000300.SS",
    "Sensex":           "^BSESN",
    "Nifty 50":         "^NSEI",
    "KOSPI":            "^KS11",
    "TWII":             "^TWII",
    "STI Singapore":    "^STI",
    "ASX 200":          "^AXJO",
    "NZX 50":           "^NZ50",
    "SET Thailand":     "^SET.BK",
    "JKSE Indonesia":   "^JKSE",
    # Commodities
    "Gold":             "GC=F",
    "Silver":           "SI=F",
    "Crude Oil (WTI)":  "CL=F",
    "Brent Crude":      "BZ=F",
    "Natural Gas":      "NG=F",
    "Copper":           "HG=F",
    "Corn":             "ZC=F",
    "Wheat":            "ZW=F",
    # Crypto
    "Bitcoin":          "BTC-USD",
    "Ethereum":         "ETH-USD",
    "Solana":           "SOL-USD",
    "XRP":              "XRP-USD",
    # Bonds
    "US 10Y Treasury":  "^TNX",
    "US 2Y Treasury":   "^IRX",
    "US 30Y Treasury":  "^TYX",
    # FX
    "EUR/USD":          "EURUSD=X",
    "GBP/USD":          "GBPUSD=X",
    "USD/JPY":          "JPY=X",
    "USD/CNY":          "CNY=X",
}

INDICES_BY_REGION = {
    "🌎 Americas":       ["S&P 500", "NASDAQ Comp.", "Dow Jones", "Russell 2000", "VIX", "TSX Composite", "Bovespa", "IPC Mexico"],
    "🌍 Europe":         ["FTSE 100", "DAX", "CAC 40", "EURO STOXX 50", "AEX", "IBEX 35", "FTSE MIB", "SMI", "OMX Stockholm", "OBX"],
    "🌏 Asia-Pacific":   ["Nikkei 225", "Hang Seng", "Shanghai Comp.", "CSI 300", "Sensex", "Nifty 50", "KOSPI", "TWII", "ASX 200", "STI Singapore"],
    "₿ Crypto":          ["Bitcoin", "Ethereum", "Solana", "XRP"],
    "🛢️ Commodities":    ["Gold", "Silver", "Crude Oil (WTI)", "Brent Crude", "Natural Gas", "Copper"],
    "💱 FX":             ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CNY"],
    "🏛️ Bonds":          ["US 10Y Treasury", "US 2Y Treasury", "US 30Y Treasury"],
}

# ─── Currencies ──────────────────────────────────────────────────────────────

CURRENCY_SYMBOLS: Dict[str, str] = {
    "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "CNY": "¥",
    "HKD": "HK$", "INR": "₹", "KRW": "₩", "TWD": "NT$", "SGD": "S$",
    "AUD": "A$", "NZD": "NZ$", "CAD": "C$", "CHF": "Fr", "SEK": "kr",
    "NOK": "kr", "DKK": "kr", "PLN": "zł", "CZK": "Kč", "HUF": "Ft",
    "BRL": "R$", "MXN": "$", "ZAR": "R", "TRY": "₺", "RUB": "₽",
    "IDR": "Rp", "MYR": "RM", "THB": "฿", "PHP": "₱", "SAR": "﷼",
    "AED": "د.إ", "ILS": "₪", "EGP": "E£", "NGN": "₦", "KES": "KSh",
    "GBp": "p",  # pence (LSE minor unit)
}

COUNTRY_FLAGS: Dict[str, str] = {
    "US": "🇺🇸", "GB": "🇬🇧", "DE": "🇩🇪", "FR": "🇫🇷", "JP": "🇯🇵",
    "HK": "🇭🇰", "CN": "🇨🇳", "IN": "🇮🇳", "KR": "🇰🇷", "TW": "🇹🇼",
    "SG": "🇸🇬", "AU": "🇦🇺", "NZ": "🇳🇿", "CA": "🇨🇦", "BR": "🇧🇷",
    "MX": "🇲🇽", "CH": "🇨🇭", "NL": "🇳🇱", "ES": "🇪🇸", "IT": "🇮🇹",
    "SE": "🇸🇪", "NO": "🇳🇴", "DK": "🇩🇰", "FI": "🇫🇮", "PL": "🇵🇱",
    "TR": "🇹🇷", "RU": "🇷🇺", "IL": "🇮🇱", "SA": "🇸🇦", "AE": "🇦🇪",
    "ZA": "🇿🇦", "NG": "🇳🇬", "KE": "🇰🇪", "EG": "🇪🇬", "TH": "🇹🇭",
    "ID": "🇮🇩", "MY": "🇲🇾", "PH": "🇵🇭",
}

# Suffix → exchange code lookup
_SUFFIX_TO_EXCHANGE = {
    info["suffix"]: code
    for code, info in EXCHANGES.items()
    if info["suffix"]
}

# ─── Asset Type Detection ─────────────────────────────────────────────────────

def detect_asset_type(symbol: str) -> str:
    """Classify a symbol as stock/etf/crypto/forex/futures/index."""
    s = symbol.upper()
    if s.startswith("^"):
        return "index"
    if s.endswith("=X"):
        return "forex"
    if s.endswith("=F"):
        return "futures"
    crypto_suffixes = ("-USD", "-BTC", "-ETH", "-USDT", "-USDC", "-EUR", "-GBP", "-JPY")
    if any(s.endswith(sfx) for sfx in crypto_suffixes):
        return "crypto"
    # ETF heuristics (common ones)
    known_etfs = {"SPY","QQQ","IWM","EFA","EEM","AGG","BND","GLD","SLV","USO","VTI","VEA","VWO",
                  "XLK","XLF","XLV","XLE","XLY","XLP","XLI","XLB","XLRE","XLU","XLC","DIA","MDY"}
    if s in known_etfs:
        return "etf"
    return "stock"


def get_exchange_info(symbol: str) -> Dict:
    """Look up exchange metadata by symbol suffix."""
    # Extract suffix
    parts = symbol.upper().split(".")
    if len(parts) > 1:
        suffix = "." + parts[-1]
        code = _SUFFIX_TO_EXCHANGE.get(suffix)
        if code:
            return {**EXCHANGES[code], "code": code}
    return {}


def is_market_open(exchange_code: str) -> bool:
    """Check if an exchange is currently within trading hours."""
    info = EXCHANGES.get(exchange_code.upper())
    if not info:
        return False
    try:
        tz = pytz.timezone(info["timezone"])
        now = datetime.now(tz)
        # Skip weekends
        if now.weekday() >= 5:
            return False
        open_h, open_m = info["open"]
        close_h, close_m = info["close"]
        open_time = dt_time(open_h, open_m)
        close_time = dt_time(close_h, close_m)
        return open_time <= now.time() <= close_time
    except Exception:
        return False


def get_all_open_markets() -> List[str]:
    """Return list of currently open exchange codes."""
    return [code for code in EXCHANGES if is_market_open(code)]


def get_market_status(symbol: str) -> str:
    """Return 'open', 'closed', 'pre', 'post', or 'unknown' for a symbol."""
    asset = detect_asset_type(symbol)
    if asset in ("crypto", "forex"):
        return "open"  # 24/7

    exch = get_exchange_info(symbol)
    if not exch:
        # Default to NYSE/NASDAQ for bare US symbols
        if "." not in symbol and not symbol.startswith("^"):
            return "open" if is_market_open("NYSE") else "closed"
        return "unknown"

    code = exch.get("code", "")
    if is_market_open(code):
        return "open"

    # Pre/post market check for US
    if exch.get("country") == "US":
        try:
            tz = pytz.timezone("America/New_York")
            now = datetime.now(tz)
            h = now.hour
            if 4 <= h < 9 or (h == 9 and now.minute < 30):
                return "pre"
            if 16 <= h < 20:
                return "post"
        except Exception:
            pass
    return "closed"


def resolve_symbol(query: str, max_results: int = 12) -> List[Dict]:
    """
    Smart global symbol resolution.
    Accepts partial company names, exact tickers, or exchange-qualified names.
    Returns list of dicts: {symbol, name, exchange, exchange_display, asset_type, currency, flag, score}
    """
    query = query.strip()
    if not query:
        return []

    results = []
    seen_symbols = set()

    try:
        search = yf.Search(query, max_results=max_results * 2)
        raw = getattr(search, "quotes", []) or []
        for item in raw:
            sym = item.get("symbol", "")
            if not sym or sym in seen_symbols:
                continue
            seen_symbols.add(sym)
            exch_display = item.get("exchDisp", item.get("exchange", ""))
            asset = detect_asset_type(sym)
            # Override for known types
            qt = item.get("quoteType", "").upper()
            if qt == "ETF":
                asset = "etf"
            elif qt == "CRYPTOCURRENCY":
                asset = "crypto"
            elif qt == "CURRENCY":
                asset = "forex"
            elif qt == "FUTURE":
                asset = "futures"
            elif qt == "INDEX":
                asset = "index"

            exch_info = get_exchange_info(sym)
            currency = item.get("currency") or exch_info.get("currency", "USD")
            country = exch_info.get("country", "")
            flag = COUNTRY_FLAGS.get(country, "")

            results.append({
                "symbol": sym,
                "name": item.get("longname") or item.get("shortname") or sym,
                "exchange": item.get("exchange", ""),
                "exchange_display": exch_display,
                "asset_type": asset,
                "currency": currency,
                "flag": flag,
                "sector": item.get("sector", ""),
                "score": item.get("score", 0),
            })
    except Exception:
        pass

    # Sort: exact matches first, then by score descending
    query_upper = query.upper()
    results.sort(key=lambda x: (0 if x["symbol"] == query_upper else 1, -x.get("score", 0)))
    return results[:max_results]


def get_currency_symbol(currency_code: str) -> str:
    """Return currency symbol for a currency code."""
    return CURRENCY_SYMBOLS.get(currency_code, currency_code + " ")


def format_symbol_with_flag(symbol: str, exchange_code: str = "") -> str:
    """Format a symbol with its country flag emoji."""
    exch = EXCHANGES.get(exchange_code.upper(), get_exchange_info(symbol))
    country = exch.get("country", "")
    flag = COUNTRY_FLAGS.get(country, "")
    return f"{flag} {symbol}".strip()


def get_usd_rate(currency: str) -> Optional[float]:
    """Get USD conversion rate for a currency (returns None if USD or unavailable)."""
    if currency in ("USD", None, ""):
        return 1.0
    # GBp (pence) to USD
    if currency == "GBp":
        gbp_usd = get_usd_rate("GBP")
        return gbp_usd / 100 if gbp_usd else None
    fx_sym = f"{currency}USD=X"
    try:
        t = yf.Ticker(fx_sym)
        rate = t.fast_info.last_price
        return float(rate) if rate else None
    except Exception:
        return None
