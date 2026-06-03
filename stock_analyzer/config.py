from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports" / "output"

DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

CACHE_EXPIRY_HOURS = 4

DEFAULT_PERIODS = {
    "1d": "1d",
    "5d": "5d",
    "1mo": "1mo",
    "3mo": "3mo",
    "6mo": "6mo",
    "1y": "1y",
    "2y": "2y",
    "5y": "5y",
    "10y": "10y",
    "ytd": "ytd",
    "max": "max",
}

DEFAULT_INTERVALS = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "1d": "1d",
    "1wk": "1wk",
    "1mo": "1mo",
}

# Technical indicator settings
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
BB_STD = 2
ATR_PERIOD = 14
ADX_PERIOD = 14
STOCH_K = 14
STOCH_D = 3
CCI_PERIOD = 20
WILLIAMS_PERIOD = 14
MFI_PERIOD = 14
CMF_PERIOD = 20

# Moving averages
SHORT_MA = [9, 20, 50]
LONG_MA = [100, 200]

# Risk settings
RISK_FREE_RATE = 0.05  # 5% annual
TRADING_DAYS = 252
VAR_CONFIDENCE = 0.95
CVAR_CONFIDENCE = 0.99

# ML settings
ML_LOOKBACK = 60
ML_FORECAST_DAYS = 30
ML_FEATURES = [
    "returns", "log_returns", "rsi", "macd", "macd_signal", "macd_hist",
    "bb_upper", "bb_lower", "bb_width", "atr", "adx", "cci", "mfi",
    "volume_ratio", "price_momentum_5", "price_momentum_10", "price_momentum_20",
    "volatility_10", "volatility_20", "sma_ratio_20", "sma_ratio_50",
]

# Scoring weights for composite signal
SIGNAL_WEIGHTS = {
    "trend": 0.30,
    "momentum": 0.25,
    "volume": 0.15,
    "volatility": 0.15,
    "sentiment": 0.15,
}

# Pattern detection thresholds
PATTERN_LOOKBACK = 100
SUPPORT_RESISTANCE_LOOKBACK = 50
FIBONACCI_LEVELS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]

SECTOR_PEERS = {
    "Technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "TSLA", "AMD", "INTC", "CRM", "ORCL"],
    "Finance": ["JPM", "BAC", "GS", "MS", "WFC", "C", "BLK", "AXP", "V", "MA"],
    "Healthcare": ["JNJ", "UNH", "PFE", "ABBV", "MRK", "LLY", "BMY", "AMGN", "GILD", "CVS"],
    "Energy": ["XOM", "CVX", "COP", "EOG", "SLB", "PXD", "OXY", "MPC", "PSX", "VLO"],
    "Consumer": ["AMZN", "WMT", "TGT", "COST", "HD", "LOW", "NKE", "SBUX", "MCD", "YUM"],
}
