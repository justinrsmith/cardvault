# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv run fastapi dev          # Start development server (hot reload)
uv run pytest               # Run all tests
uv run pytest tests/test_cards.py::test_name  # Run a single test
uv run ruff check .         # Lint
uv run ruff format .        # Format
```

After setup, install Playwright browsers:
```bash
uv run playwright install chromium
```

## Architecture

CardVault is a personal sports card collection tracker. The full implementation plan is in `cardvault-plan.md`.

**Stack:** FastAPI + SQLModel (SQLAlchemy 2.0 + Pydantic v2) + SQLite + Jinja2 templates + HTMX frontend + Playwright scraping + APScheduler for background jobs.

**Source layout** (`src/cardvault/`):
- `main.py` — FastAPI app init, lifespan hooks, router registration
- `config.py` — pydantic-settings `Settings` class (reads from `.env`)
- `database.py` — SQLModel engine, session dependency for route injection
- `models.py` — `Card` and `PriceRecord` SQLModel table definitions
- `routers/cards.py` — CRUD routes for cards
- `routers/prices.py` — Price refresh endpoints
- `services/ebay_scraper.py` — Playwright headless scraping of eBay sold listings
- `services/pricing.py` — Value estimation (median of 5 most recent `PriceRecord` sales)
- `scheduler.py` — APScheduler nightly refresh job
- `templates/` — Jinja2 HTML with HTMX partials (`partials/card_row.html`, `partials/price_history.html`)

## Key Design Decisions

**eBay scraping:** Playwright (not requests/httpx) because eBay search results are JS-rendered. Query is built as `"{year} {brand} {player_name} {card_number} {variation}"` and appended to `https://www.ebay.com/sch/i.html?_nkw=<query>&LH_Complete=1&LH_Sold=1`. Top N results (default 10, configurable) are stored as `PriceRecord` rows.

**Estimated value:** Median of the 5 most recent `PriceRecord.sale_price` values per card.

**HTMX usage:** Three HTMX patterns — inline price refresh (swaps `partials/price_history.html`), delete card without page reload, and live search on the card list. HTML form POSTs use HTMX to swap partial responses rather than full page reloads.

**Scheduling:** APScheduler runs in-process (not a separate worker). Nightly job refreshes all cards that haven't been updated in `PRICE_REFRESH_INTERVAL_HOURS` (default 24).

**Configuration:** All settings live in `.env` and are loaded via `config.py`. See `.env.example` for available keys: `DATABASE_URL`, `EBAY_RESULTS_COUNT`, `PRICE_REFRESH_INTERVAL_HOURS`, `PLAYWRIGHT_HEADLESS`.
