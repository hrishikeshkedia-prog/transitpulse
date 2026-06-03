"""
News sentiment analysis using a keyword-based VADER-style scorer.
"""
import re
from typing import Dict, List, Optional
from datetime import datetime, timezone

POSITIVE_WORDS = {
    "strong", "beat", "beats", "surge", "surges", "jump", "jumps", "gain", "gains",
    "rise", "rises", "boost", "boosts", "record", "high", "upgrade", "upgraded",
    "outperform", "outperforms", "buy", "bullish", "profit", "profits", "growth",
    "revenue", "expand", "expands", "breakthrough", "exceed", "exceeds", "dividend",
    "raised", "increase", "increases", "positive", "optimistic", "opportunity",
    "innovative", "launch", "launches", "partnership", "win", "wins", "approval",
    "approved", "rally", "rallies", "momentum", "recover", "recovery", "milestone",
    "upbeat", "robust", "solid", "strong", "excellent", "impressive",
}

NEGATIVE_WORDS = {
    "weak", "miss", "misses", "drop", "drops", "fall", "falls", "loss", "losses",
    "decline", "declines", "cut", "cuts", "downgrade", "downgraded", "underperform",
    "sell", "bearish", "crash", "crashes", "warning", "concern", "concerns",
    "risk", "risks", "lawsuit", "investigation", "probe", "fraud", "scandal",
    "recall", "recalled", "suspend", "suspended", "layoff", "layoffs", "miss",
    "shortfall", "deficit", "debt", "default", "bankruptcy", "bankrupt",
    "negative", "pessimistic", "headwind", "challenge", "challenges",
    "plunge", "plunges", "slump", "slumps", "disappointing", "disappoints",
    "tariff", "tariffs", "fine", "penalty", "penalties", "halt", "halted",
}

INTENSIFIERS = {"very", "highly", "significantly", "sharply", "substantially", "dramatically"}
NEGATORS = {"not", "no", "never", "neither", "nor", "without", "lack", "lacking"}


def score_headline(text: str) -> float:
    """Score a headline from -1.0 (very negative) to 1.0 (very positive)."""
    if not text:
        return 0.0

    words = re.findall(r'\b[a-z]+\b', text.lower())
    score = 0.0
    n = len(words)

    for i, word in enumerate(words):
        weight = 1.0
        if i > 0 and words[i - 1] in INTENSIFIERS:
            weight = 1.5
        negate = any(words[max(0, i - 3):i].__contains__(neg) for neg in NEGATORS)

        if word in POSITIVE_WORDS:
            score += weight if not negate else -weight * 0.5
        elif word in NEGATIVE_WORDS:
            score += -weight if not negate else weight * 0.5

    return max(-1.0, min(1.0, score / max(1, n / 5)))


def analyze_news(news_items: List[Dict]) -> Dict:
    """Analyze a list of news articles and return sentiment summary."""
    if not news_items:
        return {
            "overall_score": 0.0,
            "overall_sentiment": "Neutral",
            "total_articles": 0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "articles": [],
        }

    scored = []
    for item in news_items[:20]:  # Cap at 20 articles
        title = item.get("title", "") or ""
        publisher = item.get("publisher", "") or ""

        # Age weighting
        pub_time = item.get("providerPublishTime", 0)
        if pub_time:
            pub_dt = datetime.fromtimestamp(pub_time, tz=timezone.utc)
            now = datetime.now(tz=timezone.utc)
            age_hours = (now - pub_dt).total_seconds() / 3600
            age_weight = max(0.3, 1 - age_hours / 168)  # decay over 1 week
        else:
            age_weight = 0.5

        headline_score = score_headline(title)
        weighted_score = headline_score * age_weight

        scored.append({
            "title": title,
            "publisher": publisher,
            "score": headline_score,
            "weighted_score": weighted_score,
            "sentiment": _classify(headline_score),
            "published": datetime.fromtimestamp(pub_time).strftime("%Y-%m-%d %H:%M") if pub_time else "Unknown",
            "link": item.get("link", ""),
        })

    if not scored:
        return {"overall_score": 0.0, "overall_sentiment": "Neutral", "total_articles": 0, "articles": []}

    total_weight = sum(abs(a["weighted_score"]) + 0.1 for a in scored)
    overall = sum(a["weighted_score"] * (abs(a["weighted_score"]) + 0.1) for a in scored) / total_weight

    positive = sum(1 for a in scored if a["score"] > 0.1)
    negative = sum(1 for a in scored if a["score"] < -0.1)
    neutral = len(scored) - positive - negative

    return {
        "overall_score": round(overall, 3),
        "overall_sentiment": _classify(overall),
        "total_articles": len(scored),
        "positive_count": positive,
        "negative_count": negative,
        "neutral_count": neutral,
        "sentiment_distribution": {
            "positive_pct": positive / len(scored) * 100,
            "negative_pct": negative / len(scored) * 100,
            "neutral_pct": neutral / len(scored) * 100,
        },
        "articles": scored[:10],
    }


def _classify(score: float) -> str:
    if score > 0.4:
        return "Very Positive"
    elif score > 0.1:
        return "Positive"
    elif score < -0.4:
        return "Very Negative"
    elif score < -0.1:
        return "Negative"
    else:
        return "Neutral"


def sentiment_signal(score: float) -> int:
    """Convert sentiment score to trade signal (-1, 0, 1)."""
    if score > 0.2:
        return 1
    elif score < -0.2:
        return -1
    return 0
