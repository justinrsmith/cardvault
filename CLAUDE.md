# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv run fastapi dev src/cardvault/main.py  # Start development server (hot reload)
uv run pytest               # Run all tests
uv run pytest tests/test_cards.py::test_name  # Run a single test
uv run ruff check .         # Lint
uv run ruff format .        # Format
```

## Architecture

CardVault is a personal sports card collection tracker.

**Stack:** FastAPI + SQLModel (SQLAlchemy 2.0 + Pydantic v2) + SQLite + Jinja2 templates + HTMX frontend.

**Source layout** (`src/cardvault/`):
- `main.py` — FastAPI app init, lifespan hooks, router registration
- `config.py` — pydantic-settings `Settings` class (reads from `.env`)
- `database.py` — SQLModel engine, session dependency for route injection
- `models.py` — `Card` and `PriceRecord` SQLModel table definitions
- `routers/cards.py` — CRUD routes for cards (create, read, update, delete, search, inline edit)
- `routers/prices.py` — Price refresh endpoint (`POST /cards/{id}/refresh`)
- `services/ebay_scraper.py` — eBay Browse API client (`fetch_active_listings`)
- `templates/` — Jinja2 HTML with HTMX partials

**Templates:**
- `base.html`, `index.html` — page shell and main view
- `partials/card_list.html` — renders all card rows (search target)
- `partials/card_row.html` — single card row with Edit/Delete buttons
- `partials/card_edit_row.html` — inline edit form row (Save/Cancel)
- `partials/price_history.html` — estimated value cell with ↻ refresh button

## Key Design Decisions

**eBay pricing:** Uses the eBay Browse API (`/buy/browse/v1/item_summary/search`) with `sort=newlyListed` and a `-PSA -BGS -SGC -CGC -graded` filter. Returns active listings, not sold comps. Prices fetched on card creation and on manual ↻ refresh only — no scheduler.

**Estimated value:** Mean of all stored `PriceRecord.list_price` values for the card.

**PriceRecord fields:** `list_price` (asking price), `listed_at` (eBay `itemCreationDate`), `source_url`, `fetched_at`. The relationship on `Card` is `listing_records`.

**HTMX patterns:** Inline price refresh (swaps `partials/price_history.html`), delete without page reload, live search, and inline row editing (Edit button → edit form row → Save/Cancel).

**Inline editing:** `GET /cards/{id}/edit` returns `card_edit_row.html`. Save button uses `hx-put` + `hx-include="closest tr"` (no `<form>` wrapper — invalid inside `<tr>`). Cancel uses `GET /cards/{id}` to restore the read-only row.

**Configuration:** `.env` keys: `DATABASE_URL`, `EBAY_APP_ID`, `EBAY_CLIENT_SECRET`, `EBAY_RESULTS_COUNT` (default 20). `extra="ignore"` set on Settings to tolerate additional keys in `.env`.

**Test mocking:** `conftest.py` has an autouse `mock_scraper` fixture that patches both `cardvault.routers.cards.fetch_active_listings` and `cardvault.routers.prices.fetch_active_listings` to return `[]`. Tests that need results unpack `mock_scraper` and set `return_value`.
