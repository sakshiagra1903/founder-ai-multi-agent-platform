"""
Topic Modeling Service.
Supports BERTopic (default) and Scikit-learn LDA.
Avoids LLM calls for topic discovery — uses local ML models.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from loguru import logger
from app.core.config import settings


@dataclass
class TopicResult:
    topic_id: int
    label: str
    keywords: list[str]
    frequency: int
    probability: float = 0.0


class TopicModelingService:
    """
    Discovers latent topics in customer feedback.
    Uses BERTopic (preferred) or LDA depending on settings.
    Model is cached after first fit.
    """

    _model = None
    _model_type: str = ""
    _vectorizer = None

    def _fit_bertopic(self, texts: list[str]) -> list[TopicResult]:
        from bertopic import BERTopic
        from sentence_transformers import SentenceTransformer
        from sklearn.feature_extraction.text import CountVectorizer

        logger.info("Fitting BERTopic model...")
        sentence_model = SentenceTransformer(settings.embedding_model)
        vectorizer = CountVectorizer(
            stop_words="english",
            min_df=2,
            ngram_range=(1, 2),
        )
        self._model = BERTopic(
            embedding_model=sentence_model,
            vectorizer_model=vectorizer,
            nr_topics="auto",
            verbose=False,
        )
        topics, probs = self._model.fit_transform(texts)
        self._model_type = "bertopic"

        topic_info = self._model.get_topic_info()
        results: list[TopicResult] = []
        for _, row in topic_info.iterrows():
            tid = int(row["Topic"])
            if tid == -1:  # outlier topic
                continue
            topic_words = self._model.get_topic(tid)
            keywords = [w for w, _ in topic_words[:8]] if topic_words else []
            label = self._auto_label(keywords)
            results.append(TopicResult(
                topic_id=tid,
                label=label,
                keywords=keywords,
                frequency=int(row["Count"]),
            ))
        return sorted(results, key=lambda r: r.frequency, reverse=True)

    def _fit_lda(self, texts: list[str], n_topics: int = 10) -> list[TopicResult]:
        from sklearn.decomposition import LatentDirichletAllocation
        from sklearn.feature_extraction.text import TfidfVectorizer

        logger.info("Fitting LDA model...")
        self._vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words="english",
            min_df=2,
            ngram_range=(1, 2),
        )
        X = self._vectorizer.fit_transform(texts)
        feature_names = self._vectorizer.get_feature_names_out()

        self._model = LatentDirichletAllocation(
            n_components=n_topics,
            max_iter=20,
            learning_method="online",
            random_state=42,
        )
        self._model.fit(X)
        self._model_type = "lda"

        results: list[TopicResult] = []
        for i, component in enumerate(self._model.components_):
            top_indices = component.argsort()[-8:][::-1]
            keywords = [feature_names[j] for j in top_indices]
            label = self._auto_label(keywords)
            # Estimate frequency as component weight
            freq = int(component.sum() / self._model.components_.sum() * len(texts))
            results.append(TopicResult(topic_id=i, label=label, keywords=keywords, frequency=freq))
        return sorted(results, key=lambda r: r.frequency, reverse=True)

    def _auto_label(self, keywords: list[str]) -> str:
        """Auto-generate a human-readable topic label from top keywords."""
        # Map common keyword patterns to readable labels
        label_map = {
            frozenset(["pay", "payment", "billing", "charge"]): "Billing & Payments",
            frozenset(["crash", "error", "bug", "fix", "broken"]): "App Stability",
            frozenset(["slow", "speed", "performance", "fast", "load"]): "Performance",
            frozenset(["ui", "design", "interface", "look", "feel"]): "UI/UX Design",
            frozenset(["support", "help", "customer", "response", "team"]): "Customer Support",
            frozenset(["feature", "request", "add", "want", "need"]): "Feature Requests",
            frozenset(["login", "password", "account", "access", "sign"]): "Authentication",
            frozenset(["mobile", "app", "ios", "android", "phone"]): "Mobile Experience",
            frozenset(["export", "import", "data", "download", "file"]): "Data Management",
            frozenset(["security", "privacy", "data", "breach", "gdpr"]): "Security & Privacy",
            frozenset(["notification", "alert", "email", "push", "message"]): "Notifications",
        }
        kw_set = set(keywords[:5])
        for key_terms, label in label_map.items():
            if kw_set & key_terms:
                return label
        # Default: capitalize first two keywords
        return " & ".join(k.title() for k in keywords[:2]) if len(keywords) >= 2 else keywords[0].title()

    def fit(self, texts: list[str]) -> list[TopicResult]:
        """Fit topic model on a list of cleaned feedback texts."""
        if len(texts) < 5:
            logger.warning("Too few texts for topic modeling, skipping")
            return []
        try:
            if settings.topic_model_type == "bertopic":
                return self._fit_bertopic(texts)
            else:
                return self._fit_lda(texts)
        except Exception as e:
            logger.error(f"Topic modeling failed: {e}, trying LDA fallback")
            try:
                return self._fit_lda(texts)
            except Exception as e2:
                logger.error(f"LDA fallback also failed: {e2}")
                return []

    def get_document_topics(self, texts: list[str]) -> list[int]:
        """Get topic assignments for new texts (after fit)."""
        if self._model is None:
            return [-1] * len(texts)
        try:
            if self._model_type == "bertopic":
                topics, _ = self._model.transform(texts)
                return list(topics)
            else:
                X = self._vectorizer.transform(texts)
                dist = self._model.transform(X)
                return list(dist.argmax(axis=1))
        except Exception as e:
            logger.error(f"Topic assignment failed: {e}")
            return [-1] * len(texts)


topic_modeling_service = TopicModelingService()
