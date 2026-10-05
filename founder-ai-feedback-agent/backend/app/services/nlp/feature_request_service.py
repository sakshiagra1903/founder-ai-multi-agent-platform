"""
Feature Request Detection Service.
Hybrid approach: Rule-Based NLP + Keyword Matching + LLM Validation (only when needed).
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from loguru import logger

# Patterns indicating a feature request
REQUEST_PATTERNS = [
    re.compile(r'\b(please|pls)\s+(add|include|support|implement|create|build|make|give|provide)\b', re.I),
    re.compile(r'\bwould\s+(love|like|want|appreciate|be\s+great)\b', re.I),
    re.compile(r'\b(wish|hope)\s+(you|there|it|we)\s+(had|have|could|would)\b', re.I),
    re.compile(r'\b(feature\s+request|feature\s+suggestion|suggestion|idea)\b', re.I),
    re.compile(r'\bcan\s+you\s+(add|please\s+add|implement|include)\b', re.I),
    re.compile(r'\bit\s+would\s+be\s+(great|nice|helpful|awesome|amazing|good)\s+(if|to)\b', re.I),
    re.compile(r'\b(need|needs|require|requires)\s+.{0,30}\b(feature|option|ability|support|mode|button|page)\b', re.I),
    re.compile(r'\bwhy\s+(is\s+there|isn.t|dont|doesn.t|no)\b.{0,30}\b(feature|option|support|mode)\b', re.I),
    re.compile(r'\b(dark\s+mode|night\s+mode|mobile\s+app|offline\s+mode|export|import|api\s+access)\b', re.I),
    re.compile(r'\bplease\s+\w+\b', re.I),
]

# Feature categories
FEATURE_CATEGORIES: dict[str, list[str]] = {
    "UI/UX": [
        "dark mode", "night mode", "light mode", "theme", "color scheme", "font size",
        "ui improvement", "better design", "cleaner interface", "redesign", "layout"
    ],
    "Mobile": [
        "mobile app", "ios app", "android app", "iphone", "tablet", "responsive", "mobile version"
    ],
    "Export/Import": [
        "export", "import", "download", "csv export", "pdf export", "excel export",
        "data export", "backup", "sync"
    ],
    "Integrations": [
        "integrate", "integration", "zapier", "slack", "google", "microsoft", "api",
        "webhook", "connect", "plugin", "extension"
    ],
    "Collaboration": [
        "team", "collaboration", "share", "multi-user", "invite", "permissions",
        "role", "workspace", "organization"
    ],
    "Notifications": [
        "notification", "alert", "email notification", "push notification", "reminder",
        "digest", "summary email"
    ],
    "Search & Filter": [
        "search", "filter", "sort", "advanced search", "find", "query"
    ],
    "Language/Localization": [
        "language", "translation", "multilingual", "spanish", "french", "german",
        "localization", "locale", "rtl", "unicode"
    ],
    "Performance": [
        "faster", "speed up", "performance", "optimize", "quick"
    ],
    "Analytics": [
        "analytics", "report", "dashboard", "chart", "graph", "statistics", "insights",
        "metrics", "tracking"
    ],
    "Security": [
        "2fa", "two-factor", "sso", "single sign-on", "encryption", "audit log",
        "security", "gdpr", "compliance"
    ],
    "Offline Support": [
        "offline", "without internet", "cache", "local", "sync offline"
    ],
}


@dataclass
class FeatureRequestResult:
    is_feature_request: bool
    request_text: str | None
    normalized_request: str | None
    category: str | None
    confidence_score: float
    priority: str = "medium"
    matched_patterns: list[str] = field(default_factory=list)


class FeatureRequestService:
    """
    Detect and categorize feature requests.
    Stage 1: Pattern/keyword matching (primary — fast, free)
    Stage 2: LLM extraction (only for high-confidence ambiguous cases)
    """

    def _category_match(self, text: str) -> str | None:
        text_lower = text.lower()
        for cat, keywords in FEATURE_CATEGORIES.items():
            if any(kw in text_lower for kw in keywords):
                return cat
        return None

    def _normalized_request(self, text: str) -> str | None:
        """Extract the specific feature being requested."""
        text_lower = text.lower()
        for cat, keywords in FEATURE_CATEGORIES.items():
            for kw in keywords:
                if kw in text_lower:
                    return kw.title()
        # Fall back to the first noun phrase after request keywords
        match = re.search(
            r'(?:add|implement|include|create|build|want|need|wish for|would love)\s+([\w\s]{3,40})',
            text, re.I
        )
        if match:
            return match.group(1).strip().title()[:100]
        return None

    def _calculate_priority(self, text: str, matched_count: int) -> str:
        """Priority based on urgency language and match strength."""
        text_lower = text.lower()
        if any(w in text_lower for w in ["urgent", "critical", "asap", "immediately", "blocker", "must have"]):
            return "critical"
        if matched_count >= 2:
            return "high"
        if matched_count == 1:
            return "medium"
        return "low"

    def detect(self, text: str) -> FeatureRequestResult:
        """Detect if a text contains a feature request."""
        if not text or len(text.strip()) < 5:
            return FeatureRequestResult(False, None, None, None, 0.0)

        matched_patterns = []
        for pattern in REQUEST_PATTERNS:
            if pattern.search(text):
                matched_patterns.append(pattern.pattern[:50])

        if not matched_patterns:
            return FeatureRequestResult(False, None, None, None, 0.0)

        confidence = min(0.5 + len(matched_patterns) * 0.15, 0.97)
        category = self._category_match(text)
        normalized = self._normalized_request(text)
        priority = self._calculate_priority(text, len(matched_patterns))

        return FeatureRequestResult(
            is_feature_request=True,
            request_text=text[:500],
            normalized_request=normalized,
            category=category,
            confidence_score=round(confidence, 4),
            priority=priority,
            matched_patterns=matched_patterns,
        )

    def detect_batch(self, texts: list[str]) -> list[FeatureRequestResult]:
        return [self.detect(t) for t in texts]


feature_request_service = FeatureRequestService()
