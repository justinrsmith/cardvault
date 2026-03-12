"""Tests for Settings config."""

import pytest

from cardvault.config import Settings


def test_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.TempPathFactory) -> None:
    monkeypatch.chdir(tmp_path)
    s = Settings()
    assert s.database_url == "sqlite:///./cardvault.db"
    assert s.ebay_app_id == ""
    assert s.ebay_client_secret == ""
    assert s.ebay_results_count == 20


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EBAY_APP_ID", "test-app-id")
    monkeypatch.setenv("EBAY_CLIENT_SECRET", "test-secret")
    monkeypatch.setenv("EBAY_RESULTS_COUNT", "5")
    s = Settings()
    assert s.ebay_app_id == "test-app-id"
    assert s.ebay_client_secret == "test-secret"
    assert s.ebay_results_count == 5
