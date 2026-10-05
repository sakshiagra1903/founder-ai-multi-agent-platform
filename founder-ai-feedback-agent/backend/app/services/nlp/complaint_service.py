"""
Complaint Detection Service.
Uses Sentence Transformers + semantic similarity + rule-based classification.
No LLM calls per record — fast and free.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from loguru import logger
from app.core.config import settings


COMPLAINT_CATEGORIES: dict[str, dict] = {
    "Payment Issues": {
        "keywords": [
            "payment", "charge", "billing", "invoice", "refund", "transaction",
            "credit card", "debit", "subscription charge", "overcharged", "double charged",
            "payment failed", "payment error", "cannot pay", "payment gateway"
        ],
        "severity": "critical",
        "subcategories": ["Payment Failure", "Overcharge", "Refund Issue", "Billing Error"],
    },
    "Login Problems": {
        "keywords": [
            "login", "log in", "sign in", "password", "reset password", "forgot password",
            "cannot login", "can't login", "authentication", "access denied", "locked out",
            "account locked", "2fa", "two factor", "otp", "verification"
        ],
        "severity": "high",
        "subcategories": ["Password Reset", "Account Locked", "2FA Issue", "Session Expired"],
    },
    "Performance Issues": {
        "keywords": [
            "slow", "lag", "loading", "freeze", "crash", "unresponsive", "timeout",
            "takes forever", "spinning", "buffering", "sluggish", "not loading",
            "keeps crashing", "hangs", "freezes", "performance"
        ],
        "severity": "high",
        "subcategories": ["App Crash", "Slow Loading", "Timeout", "Freeze"],
    },
    "UI/UX Problems": {
        "keywords": [
            "confusing", "hard to use", "difficult", "not intuitive", "ugly",
            "broken ui", "layout", "design", "button", "navigation", "menu",
            "interface", "ux", "user experience", "cluttered", "overwhelming"
        ],
        "severity": "medium",
        "subcategories": ["Navigation Issue", "Design Problem", "Accessibility", "Broken UI"],
    },
    "Customer Support Issues": {
        "keywords": [
            "support", "help desk", "customer service", "no response", "rude",
            "unhelpful", "ignored", "waiting", "ticket", "resolution",
            "no one helped", "terrible support", "bad support", "slow response"
        ],
        "severity": "high",
        "subcategories": ["Slow Response", "No Response", "Unhelpful", "Rude Support"],
    },
    "App Crashes": {
        "keywords": [
            "crash", "crashes", "force close", "app stopped", "unexpected error",
            "runtime error", "error 500", "server error", "internal error",
            "app died", "sudden close", "fatal error"
        ],
        "severity": "critical",
        "subcategories": ["Fatal Crash", "Random Crash", "Startup Crash"],
    },
    "Subscription Problems": {
        "keywords": [
            "subscription", "cancel", "cancellation", "unsubscribe", "downgrade",
            "upgrade", "plan", "tier", "premium", "pro plan", "free trial",
            "auto renew", "auto-renew", "cannot cancel"
        ],
        "severity": "high",
        "subcategories": ["Cancellation Issue", "Upgrade Problem", "Trial Issue"],
    },
    "Data/Privacy Issues": {
        "keywords": [
            "data lost", "data missing", "deleted", "lost my data", "privacy",
            "security", "breach", "hack", "leaked", "gdpr", "personal data",
            "delete my account", "data export"
        ],
        "severity": "critical",
        "subcategories": ["Data Loss", "Privacy Concern", "Security Breach", "Data Export"],
    },
}


@dataclass
class ComplaintDetectionResult:
    is_complaint: bool
    category: str | None
    subcategory: str | None
    severity: str | None
    confidence_score: float
    matched_keywords: list[str] = field(default_factory=list)
    description: str | None = None


class ComplaintService:
    """
    Two-stage complaint detection:
    1. Fast keyword matching (primary)
    2. Semantic similarity via Sentence Transformers (refinement)
    """

    _encoder = None
    _category_embeddings: dict = {}

    def _load_encoder(self) -> None:
        if self._encoder is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self._encoder = SentenceTransformer(settings.embedding_model)
            # Pre-compute category embeddings for fast similarity
            for category, info in COMPLAINT_CATEGORIES.items():
                cat_text = f"{category}: {', '.join(info['keywords'][:5])}"
                self._category_embeddings[category] = self._encoder.encode(cat_text)
            logger.info("Complaint encoder ready")
        except Exception as e:
            logger.warning(f"Sentence transformer not available: {e}. Using keyword-only mode.")
            self._encoder = None

    def _keyword_match(self, text: str) -> tuple[str | None, str | None, float, list[str]]:
        """Fast keyword matching — O(n) check."""
        text_lower = text.lower()
        best_category = None
        best_subcat = None
        best_score = 0.0
        best_keywords: list[str] = []

        for category, info in COMPLAINT_CATEGORIES.items():
            matched = [kw for kw in info["keywords"] if kw in text_lower]
            if matched:
                score = len(matched) / len(info["keywords"])
                if score > best_score:
                    best_score = score
                    best_category = category
                    best_keywords = matched
                    # Find best subcategory
                    for sub in info.get("subcategories", []):
                        if sub.lower() in text_lower:
                            best_subcat = sub
                            break

        return best_category, best_subcat, min(best_score * 3, 0.95), best_keywords

    def _semantic_match(self, text: str) -> tuple[str | None, float]:
        """Semantic similarity matching using embeddings."""
        if self._encoder is None or not self._category_embeddings:
            return None, 0.0
        from sentence_transformers import util
        import torch
        text_emb = self._encoder.encode(text)
        best_cat = None
        best_sim = 0.0
        for category, cat_emb in self._category_embeddings.items():
            sim = float(util.cos_sim(text_emb, cat_emb))
            if sim > best_sim:
                best_sim = sim
                best_cat = category
        return best_cat, best_sim

    def detect(self, text: str) -> ComplaintDetectionResult:
        """Detect complaints in a single feedback text."""
        self._load_encoder()
        if not text or len(text.strip()) < 5:
            return ComplaintDetectionResult(False, None, None, None, 0.0)

        # Stage 1: keyword
        kw_cat, kw_sub, kw_score, matched_kws = self._keyword_match(text)

        # Stage 2: semantic (if encoder available)
        sem_cat, sem_score = self._semantic_match(text)

        # Combine: keyword wins if score high enough, else use semantic
        if kw_score >= 0.15:
            final_cat = kw_cat
            final_score = min(kw_score + sem_score * 0.2, 0.99)
        elif sem_score >= 0.5:
            final_cat = sem_cat
            final_score = sem_score * 0.8
        else:
            return ComplaintDetectionResult(False, None, None, None, max(kw_score, sem_score))

        severity = COMPLAINT_CATEGORIES.get(final_cat, {}).get("severity", "medium")
        return ComplaintDetectionResult(
            is_complaint=True,
            category=final_cat,
            subcategory=kw_sub,
            severity=severity,
            confidence_score=round(final_score, 4),
            matched_keywords=matched_kws,
            description=f"Detected: {final_cat}" + (f" > {kw_sub}" if kw_sub else ""),
        )

    def detect_batch(self, texts: list[str]) -> list[ComplaintDetectionResult]:
        """Batch complaint detection."""
        self._load_encoder()
        return [self.detect(text) for text in texts]


complaint_service = ComplaintService()
