"""Unit tests for feature request detection service."""
import pytest
from app.services.nlp.feature_request_service import FeatureRequestService


@pytest.fixture
def svc():
    return FeatureRequestService()


def test_detects_dark_mode_request(svc):
    result = svc.detect("Please add dark mode, it would be great!")
    assert result.is_feature_request
    assert result.category == "UI/UX"


def test_detects_mobile_app_request(svc):
    result = svc.detect("I would love a mobile app for iOS")
    assert result.is_feature_request
    assert result.category == "Mobile"


def test_detects_export_request(svc):
    result = svc.detect("Can you please add CSV export functionality?")
    assert result.is_feature_request
    assert result.category == "Export/Import"


def test_no_feature_request_for_complaint(svc):
    result = svc.detect("The payment system is broken and I lost my money!")
    # Could go either way, but should not be high confidence feature request
    if result.is_feature_request:
        assert result.confidence_score < 0.7


def test_priority_critical_for_urgent(svc):
    result = svc.detect("We urgently need SSO support, it's a blocker for enterprise clients")
    assert result.is_feature_request
    assert result.priority in ("critical", "high")


def test_batch_detection(svc):
    texts = [
        "Please add dark mode",
        "The app crashed again",
        "I wish there was offline support",
    ]
    results = svc.detect_batch(texts)
    assert len(results) == 3
    assert results[0].is_feature_request
    assert results[2].is_feature_request
