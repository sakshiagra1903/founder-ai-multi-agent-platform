"""Unit tests for preprocessing service."""
import pytest
import pandas as pd
from app.services.preprocessing_service import PreprocessingService


@pytest.fixture
def svc():
    return PreprocessingService()


def test_clean_text_removes_urls(svc):
    text = "Check out https://example.com for more info"
    result = svc.clean_text(text)
    assert "https" not in result
    assert "example.com" not in result


def test_clean_text_returns_none_for_empty(svc):
    assert svc.clean_text("") is None
    assert svc.clean_text("   ") is None
    assert svc.clean_text(None) is None


def test_fingerprint_is_consistent(svc):
    t1 = svc.fingerprint("Hello World")
    t2 = svc.fingerprint("hello world")
    assert t1 == t2  # case-insensitive


def test_fingerprint_different_texts(svc):
    assert svc.fingerprint("foo bar") != svc.fingerprint("baz qux")


def test_process_dataframe_removes_duplicates(svc):
    df = pd.DataFrame({
        "feedback_text": ["Great app!", "Great app!", "Terrible service"],
        "rating": [5, 5, 1],
    })
    result = svc.process_dataframe(df)
    assert result["stats"]["duplicates_removed"] == 1
    assert result["stats"]["cleaned_count"] == 2


def test_process_dataframe_removes_empty(svc):
    df = pd.DataFrame({"feedback_text": ["Good app", "", None, "  "]})
    result = svc.process_dataframe(df)
    assert result["stats"]["empty_removed"] >= 3


def test_process_dataframe_renames_columns(svc):
    df = pd.DataFrame({"text": ["Nice product"], "score": [4]})
    result = svc.process_dataframe(df)
    assert "feedback_text" in result["dataframe"].columns
    assert "rating" in result["dataframe"].columns


def test_normalize_rating_above_5(svc):
    df = pd.DataFrame({"feedback_text": ["Good", "Bad"], "rating": [8.0, 4.0]})
    result = svc.process_dataframe(df)
    assert result["dataframe"]["rating"].max() <= 5.0
