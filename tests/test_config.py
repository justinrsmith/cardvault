"""Tests for Settings config."""

import pytest

from cardvault.config import Settings


def test_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.TempPathFactory) -> None:
    monkeypatch.chdir(tmp_path)
    s = Settings()
    assert s.database_url == "sqlite:///./cardvault.db"
    assert s.ebay_results_count == 10
    assert s.price_refresh_interval_hours == 24
    assert s.playwright_headless is True


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EBAY_RESULTS_COUNT", "5")
    monkeypatch.setenv("PLAYWRIGHT_HEADLESS", "false")
    s = Settings()
    assert s.ebay_results_count == 5
    assert s.playwright_headless is False
