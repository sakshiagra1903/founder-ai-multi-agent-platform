"""
Sentiment Analysis Service — uses FREE HuggingFace models.
Primary: cardiffnlp/twitter-roberta-base-sentiment-latest
Fallback: distilbert-base-uncased-finetuned-sst-2-english

Does NOT call an LLM for every prediction — uses local inference.
"""
from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Any
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings


@dataclass
class SentimentScore:
    label: str          # "positive" | "neutral" | "negative"
    confidence: float
    positive_score: float
    neutral_score: float
    negative_score: float
    model_used: str


class SentimentService:
    """
    Local sentiment inference with HuggingFace transformers.
    Model is loaded once and cached in memory.
    Batch processing supported for efficiency.
    """

    _pipeline = None
    _model_name: str = ""

    def _load_model(self) -> None:
        if self._pipeline is not None:
            return
        from transformers import pipeline
        model_name = settings.sentiment_model
        logger.info(f"Loading sentiment model: {model_name}")
        try:
            self._pipeline = pipeline(
                "text-classification",
                model=model_name,
                top_k=None,          # return all class scores
                truncation=True,
                max_length=512,
            )
            self._model_name = model_name
            logger.info(f"Sentiment model loaded: {model_name}")
        except Exception as e:
            logger.warning(f"Primary model failed ({e}), falling back to DistilBERT")
            fallback = "distilbert-base-uncased-finetuned-sst-2-english"
            self._pipeline = pipeline(
                "text-classification",
                model=fallback,
                top_k=None,
                truncation=True,
                max_length=512,
            )
            self._model_name = fallback

    def _normalize_label(self, raw_label: str) -> str:
        """Normalize model-specific labels to positive/neutral/negative."""
        label = raw_label.lower()
        # RoBERTa twitter uses: LABEL_0=negative, LABEL_1=neutral, LABEL_2=positive
        mapping = {
            "label_0": "negative",
            "label_1": "neutral",
            "label_2": "positive",
            # DistilBERT uses POSITIVE / NEGATIVE (no neutral)
            "positive": "positive",
            "negative": "negative",
            "neutral": "neutral",
        }
        return mapping.get(label, "neutral")

    def analyze_single(self, text: str) -> SentimentScore:
        """Analyze a single feedback text."""
        self._load_model()
        if not text or len(text.strip()) < 3:
            return SentimentScore("neutral", 1.0, 0.0, 1.0, 0.0, self._model_name)

        results = self._pipeline(text[:512])[0]  # list of {label, score}
        scores = {self._normalize_label(r["label"]): r["score"] for r in results}

        pos = scores.get("positive", 0.0)
        neu = scores.get("neutral", 0.0)
        neg = scores.get("negative", 0.0)

        # DistilBERT has no neutral — derive it
        if neu == 0.0 and (pos + neg) > 0:
            # Treat low-confidence predictions as neutral
            if max(pos, neg) < 0.65:
                neu = 1.0 - pos - neg
                if pos > neg:
                    pos -= neu / 2
                else:
                    neg -= neu / 2

        # Determine dominant label
        dominant_label = max(scores, key=scores.get)
        confidence = scores[dominant_label]

        return SentimentScore(
            label=dominant_label,
            confidence=round(confidence, 4),
            positive_score=round(pos, 4),
            neutral_score=round(neu, 4),
            negative_score=round(neg, 4),
            model_used=self._model_name,
        )

    def analyze_batch(self, texts: list[str], batch_size: int = 32) -> list[SentimentScore]:
        """Batch analyze texts — efficient for bulk ingestion."""
        self._load_model()
        results = []
        for i in range(0, len(texts), batch_size):
            batch = [t[:512] for t in texts[i:i + batch_size]]
            try:
                raw_batch = self._pipeline(batch)
                for raw in raw_batch:
                    scores = {self._normalize_label(r["label"]): r["score"] for r in raw}
                    pos = scores.get("positive", 0.0)
                    neu = scores.get("neutral", 0.0)
                    neg = scores.get("negative", 0.0)
                    dominant = max(scores, key=scores.get)
                    results.append(SentimentScore(
                        label=dominant,
                        confidence=round(scores[dominant], 4),
                        positive_score=round(pos, 4),
                        neutral_score=round(neu, 4),
                        negative_score=round(neg, 4),
                        model_used=self._model_name,
                    ))
            except Exception as e:
                logger.error(f"Batch sentiment error: {e}")
                for _ in batch:
                    results.append(SentimentScore("neutral", 0.5, 0.33, 0.34, 0.33, "error"))
        return results


sentiment_service = SentimentService()
