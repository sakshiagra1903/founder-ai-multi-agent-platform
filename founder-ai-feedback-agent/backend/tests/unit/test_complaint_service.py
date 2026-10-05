"""Unit tests for complaint detection service."""
import pytest
from app.services.nlp.complaint_service import ComplaintService


@pytest.fixture
def svc():
    return ComplaintService()


def test_detects_payment_complaint(svc):
    result = svc.detect("My payment failed and I was charged twice!")
    assert result.is_complaint
    assert "Payment" in result.category


def test_detects_login_complaint(svc):
    result = svc.detect("I cannot login, my password reset isn't working")
    assert result.is_complaint
    assert "Login" in result.category


def test_detects_performance_complaint(svc):
    result = svc.detect("The app is extremely slow, it keeps freezing and lagging")
    assert result.is_complaint
    assert "Performance" in result.category or "App Crash" in result.category


def test_no_complaint_for_positive(svc):
    result = svc.detect("I absolutely love this product, it's fantastic!")
    assert not result.is_complaint


def test_empty_text(svc):
    result = svc.detect("")
    assert not result.is_complaint


def test_batch_detection(svc):
    texts = [
        "Payment failed again!",
        "Great product, loving it",
        "App keeps crashing on startup",
    ]
    results = svc.detect_batch(texts)
    assert len(results) == 3
    assert results[0].is_complaint
    assert not results[1].is_complaint
    assert results[2].is_complaint
