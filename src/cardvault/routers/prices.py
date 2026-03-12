from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from cardvault.config import settings
from cardvault.database import get_session
from cardvault.models import Card, PriceRecord
from cardvault.services.ebay_scraper import fetch_active_listings

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


@router.post("/cards/{card_id}/refresh", response_class=HTMLResponse)
async def refresh_card_prices(
    card_id: int,
    request: Request,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    card = session.get(Card, card_id)
    if not card:
        return HTMLResponse(status_code=404)

    try:
        results = await fetch_active_listings(
            card.search_query,
            settings.ebay_results_count,
        )
        # Replace existing records with a fresh market snapshot
        for record in card.listing_records:
            session.delete(record)
        session.flush()
        for r in results:
            session.add(PriceRecord(card_id=card.id, **r))
        session.commit()
        session.refresh(card)
    except Exception:
        pass  # render the partial with whatever data exists

    return templates.TemplateResponse(request, "partials/price_history.html", {"card": card})
