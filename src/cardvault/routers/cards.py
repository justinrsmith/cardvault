from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from cardvault.config import settings
from cardvault.database import get_session
from cardvault.models import Card, PriceRecord
from cardvault.services.ebay_scraper import scrape_sold_listings

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent.parent / "templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request, session: Session = Depends(get_session)) -> HTMLResponse:
    cards = session.exec(select(Card).order_by(Card.created_at.desc())).all()
    return templates.TemplateResponse(request, "index.html", {"cards": cards})


@router.post("/cards", response_class=HTMLResponse)
async def create_card(
    request: Request,
    year: int = Form(...),
    player_name: str = Form(...),
    brand: str = Form(...),
    set: str = Form(...),
    card_number: str = Form(""),
    variation: str = Form(""),
    notes: str = Form(""),
    session: Session = Depends(get_session),
) -> HTMLResponse:
    card = Card(
        year=year,
        player_name=player_name,
        brand=brand,
        set=set,
        card_number=card_number,
        variation=variation,
        notes=notes,
    )
    session.add(card)
    session.commit()
    session.refresh(card)

    try:
        results = await scrape_sold_listings(
            card.search_query,
            settings.ebay_results_count,
        )
        for r in results:
            session.add(PriceRecord(card_id=card.id, **r))
        session.commit()
        session.refresh(card)
    except Exception:
        pass  # render the row with whatever data we have

    return templates.TemplateResponse(request, "partials/card_row.html", {"card": card})


@router.delete("/cards/{card_id}", response_class=HTMLResponse)
def delete_card(card_id: int, session: Session = Depends(get_session)) -> HTMLResponse:
    card = session.get(Card, card_id)
    if card:
        session.delete(card)
        session.commit()
    return HTMLResponse("")


@router.get("/cards/search", response_class=HTMLResponse)
def search_cards(
    request: Request,
    q: str = "",
    session: Session = Depends(get_session),
) -> HTMLResponse:
    query = select(Card).order_by(Card.created_at.desc())
    if q:
        term = f"%{q}%"
        query = query.where(
            Card.player_name.ilike(term)  # type: ignore[union-attr]
            | Card.brand.ilike(term)  # type: ignore[union-attr]
            | Card.set.ilike(term)  # type: ignore[union-attr]
            | Card.card_number.ilike(term)  # type: ignore[union-attr]
        )
    cards = session.exec(query).all()
    return templates.TemplateResponse(request, "partials/card_list.html", {"cards": cards})
