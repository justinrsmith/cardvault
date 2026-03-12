from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    pass


class Card(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    player_name: str = Field(index=True)
    year: int
    brand: str
    set: str
    card_number: str = ""
    variation: str = ""
    notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    listing_records: list[PriceRecord] = Relationship(back_populates="card")

    @property
    def estimated_value(self) -> float | None:
        """Mean of all stored listing prices."""
        if not self.listing_records:
            return None
        return sum(r.list_price for r in self.listing_records) / len(self.listing_records)

    @property
    def search_query(self) -> str:
        """eBay search string for this card."""
        parts = [str(self.year), self.brand, self.set, self.player_name]
        if self.card_number:
            parts.append(self.card_number)
        if self.variation:
            parts.append(self.variation)
        return " ".join(parts)


class PriceRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    card_id: int = Field(foreign_key="card.id", index=True)
    list_price: float
    listed_at: datetime
    source_url: str = ""
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    card: Card | None = Relationship(back_populates="listing_records")
