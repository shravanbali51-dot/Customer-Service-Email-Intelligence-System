from dataclasses import dataclass
import re


INTENT_SIGNALS = {
    "Complaint": {
        "damaged": 4,
        "broken": 4,
        "defective": 4,
        "bad experience": 4,
        "frustrated": 3,
        "angry": 3,
        "complaint": 5,
        "unacceptable": 4,
        "not working": 4,
        "terrible": 3,
        "issue": 1,
    },
    "Refund": {
        "refund": 6,
        "money back": 6,
        "chargeback": 5,
        "cancelled": 3,
        "canceled": 3,
        "billing": 2,
        "charged": 3,
        "invoice": 2,
        "subscription": 2,
        "return": 2,
    },
    "Product Inquiry": {
        "pricing": 4,
        "feature": 3,
        "features": 3,
        "demo": 4,
        "trial": 3,
        "available": 2,
        "support": 1,
        "integrate": 3,
        "bulk": 3,
        "plan": 2,
        "question": 2,
    },
    "Delivery Issue": {
        "delivery": 5,
        "delivered": 3,
        "shipping": 4,
        "shipment": 4,
        "tracking": 4,
        "package": 3,
        "late": 3,
        "arrived": 2,
        "missing": 4,
        "courier": 3,
    },
    "Technical Issue": {
        "account": 5,
        "login": 4,
        "password": 4,
        "reset": 4,
        "locked": 4,
        "access": 3,
        "sign in": 4,
        "signin": 4,
        "verification": 3,
        "profile": 2,
    },
    "Feedback": {
        "feedback": 5,
        "suggestion": 4,
        "thank": 3,
        "thanks": 3,
        "great": 2,
        "love": 3,
        "appreciate": 3,
        "improve": 2,
        "recommend": 3,
    },
}

SPAM_SIGNALS = {
    "free money": 6,
    "winner": 5,
    "congratulations": 3,
    "limited time offer": 5,
    "click here": 4,
    "buy now": 4,
    "crypto": 4,
    "bitcoin": 4,
    "wire transfer": 5,
    "lottery": 6,
    "claim your prize": 7,
    "risk free": 4,
    "act now": 4,
    "guaranteed income": 7,
    "http://": 3,
    "https://": 2,
}

POSITIVE_WORDS = {
    "amazing",
    "appreciate",
    "awesome",
    "excellent",
    "fast",
    "good",
    "great",
    "happy",
    "helpful",
    "impressed",
    "love",
    "perfect",
    "resolved",
    "smooth",
    "thank",
    "thanks",
}

NEGATIVE_WORDS = {
    "angry",
    "bad",
    "broken",
    "canceled",
    "cancelled",
    "cancelling",
    "charged",
    "cancel",
    "complaint",
    "damaged",
    "delay",
    "delayed",
    "disappointed",
    "failed",
    "frustrated",
    "late",
    "missing",
    "never",
    "not",
    "poor",
    "refund",
    "terrible",
    "unacceptable",
    "upset",
    "wrong",
}

URGENCY_TERMS = {
    "asap",
    "critical",
    "emergency",
    "immediately",
    "now",
    "urgent",
    "today",
    "escalate",
    "manager",
    "lawsuit",
    "chargeback",
}

NEGATIONS = {"not", "never", "no", "hardly", "barely", "without"}
INTENSIFIERS = {"very", "really", "extremely", "absolutely", "completely", "totally"}


@dataclass(frozen=True)
class AnalysisResult:
    category: str
    category_confidence: float
    sentiment: str
    sentiment_score: float
    priority: str
    priority_score: int
    is_spam: bool
    spam_score: int
    auto_reply_eligible: bool
    signals: list[str]


def analyze_email_text(subject: str, body: str) -> AnalysisResult:
    text = normalize_text(f"{subject} {body}")
    tokens = tokenize(text)
    is_spam, spam_score, spam_signals = detect_spam(text, tokens)
    category, category_confidence, category_signals = classify_intent(text)
    sentiment, sentiment_score, sentiment_signals = analyze_sentiment(tokens)
    priority, priority_score, priority_signals = assign_priority(
        text=text,
        tokens=tokens,
        category=category,
        sentiment=sentiment,
        sentiment_score=sentiment_score,
    )

    auto_reply_eligible = should_auto_reply(category, sentiment, priority, is_spam, text)
    signals = [*spam_signals, *category_signals, *sentiment_signals, *priority_signals]
    return AnalysisResult(
        category=category,
        category_confidence=category_confidence,
        sentiment=sentiment,
        sentiment_score=sentiment_score,
        priority=priority,
        priority_score=priority_score,
        is_spam=is_spam,
        spam_score=spam_score,
        auto_reply_eligible=auto_reply_eligible,
        signals=signals[:8],
    )


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text)


def classify_intent(text: str) -> tuple[str, float, list[str]]:
    scores: dict[str, int] = {}
    matched: dict[str, list[str]] = {}

    for category, signals in INTENT_SIGNALS.items():
        category_score = 0
        category_matches = []
        for phrase, weight in signals.items():
            if phrase in text:
                category_score += weight
                category_matches.append(phrase)
        scores[category] = category_score
        matched[category] = category_matches

    top_category, top_score = max(scores.items(), key=lambda item: item[1])
    if top_score == 0:
        return "Product Inquiry", 0.42, ["No strong intent keyword found"]

    score_total = sum(scores.values()) or top_score
    confidence = round(max(0.52, min(0.97, top_score / score_total)), 2)
    signals = [f"{top_category}: {phrase}" for phrase in matched[top_category][:3]]
    return top_category, confidence, signals


def detect_spam(text: str, tokens: list[str]) -> tuple[bool, int, list[str]]:
    score = 0
    signals = []
    for phrase, weight in SPAM_SIGNALS.items():
        if phrase in text:
            score += weight
            signals.append(f"spam: {phrase}")

    link_count = text.count("http://") + text.count("https://") + text.count("www.")
    if link_count >= 2:
        score += 5
        signals.append("spam: multiple links")

    if len(tokens) > 20:
        repeated_ratio = 1 - (len(set(tokens)) / len(tokens))
        if repeated_ratio >= 0.45:
            score += 5
            signals.append("spam: repeated wording")

    return score >= 7, score, signals[:3]


def analyze_sentiment(tokens: list[str]) -> tuple[str, float, list[str]]:
    score = 0.0
    signals = []
    previous = ""

    for token in tokens:
        weight = 1.0
        if previous in INTENSIFIERS:
            weight = 1.5

        if token in POSITIVE_WORDS:
            delta = weight
            if previous in NEGATIONS:
                delta *= -1
            score += delta
            signals.append(f"positive: {token}")
        elif token in NEGATIVE_WORDS:
            delta = -weight
            if previous in NEGATIONS:
                delta *= -1
            score += delta
            signals.append(f"negative: {token}")

        previous = token

    normalized = round(score / max(3, len(tokens) ** 0.5), 2)
    if normalized >= 0.35:
        return "Positive", normalized, signals[:3]
    if normalized <= -0.35:
        return "Negative", normalized, signals[:3]
    return "Neutral", normalized, signals[:3]


def assign_priority(
    *,
    text: str,
    tokens: list[str],
    category: str,
    sentiment: str,
    sentiment_score: float,
) -> tuple[str, int, list[str]]:
    score = 20
    signals = []

    if category in {"Complaint", "Refund", "Delivery Issue", "Technical Issue"}:
        score += 20
        signals.append(f"category risk: {category}")

    if category == "Complaint":
        score += 12
    elif category == "Refund":
        score += 10

    if sentiment == "Negative":
        score += 18
        signals.append("negative sentiment")
    elif sentiment == "Positive":
        score -= 8

    urgent_hits = sorted({term for term in URGENCY_TERMS if term in text or term in tokens})
    if urgent_hits:
        score += 12 + min(12, len(urgent_hits) * 4)
        signals.append(f"urgency: {', '.join(urgent_hits[:3])}")

    if sentiment_score <= -1.0:
        score += 8
    if len(tokens) > 140:
        score += 5

    score = max(0, min(100, score))
    if score >= 78:
        return "Critical", score, signals
    if score >= 58:
        return "High", score, signals
    if score >= 34:
        return "Medium", score, signals
    return "Low", score, signals


def should_auto_reply(category: str, sentiment: str, priority: str, is_spam: bool, text: str) -> bool:
    if is_spam:
        return False
    if category in {"Complaint", "Refund", "Delivery Issue", "Technical Issue"}:
        return False
    if sentiment == "Negative" or priority in {"High", "Critical"}:
        return False
    positive_or_polite = any(
        phrase in text
        for phrase in (
            "thank",
            "thanks",
            "appreciate",
            "great",
            "hello",
            "hi",
            "good morning",
            "good afternoon",
            "feedback",
        )
    )
    return category in {"Feedback", "Product Inquiry"} and positive_or_polite
