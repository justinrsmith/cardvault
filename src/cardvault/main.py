from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from cardvault.database import create_db_and_tables
from cardvault.routers import cards, prices


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    create_db_and_tables()
    yield


app = FastAPI(title="CardVault", lifespan=lifespan)
app.include_router(cards.router)
app.include_router(prices.router)
