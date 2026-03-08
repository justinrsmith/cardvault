import base64
from datetime import datetime
from typing import Any

import httpx

from cardvault.config import settings

_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
_BROWSE_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"


async def _get_access_token() -> str:
    """Fetch a client credentials OAuth token from eBay."""
    credentials = base64.b64encode(
        f"{settings.ebay_app_id}:{settings.ebay_client_secret}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            _TOKEN_URL,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope",
            },
        )
        if response.is_error:
            print(f"eBay OAuth error {response.status_code}:\n{response.text}")
        response.raise_for_status()
        return str(response.json()["access_token"])


async def scrape_sold_listings(
    query: str,
    count: int,
) -> list[dict[str, Any]]:
    """Fetch current eBay listings via the Browse API and return up to *count* results.

    Returns a list of dicts with keys: sale_price (float), sold_at (datetime),
    source_url (str). Returns [] if credentials are not configured.
    """
    if not settings.ebay_app_id or not settings.ebay_client_secret:
        return []

    token = await _get_access_token()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            _BROWSE_URL,
            headers={"Authorization": f"Bearer {token}"},
            params={
                "q": f"{query} -PSA -BGS -SGC -CGC -graded",
                "limit": str(count),
                "sort": "newlyListed",
            },
        )
        if response.is_error:
            print(f"eBay Browse API error {response.status_code}:\n{response.text}")
        response.raise_for_status()
        data = response.json()

    results: list[dict[str, Any]] = []
    for item in data.get("itemSummaries", []):
        try:
            price = float(item["price"]["value"])
            listed_at = datetime.fromisoformat(item["itemCreationDate"].replace("Z", "+00:00"))
            source_url: str = item.get("itemWebUrl", "")
            results.append({"sale_price": price, "sold_at": listed_at, "source_url": source_url})
        except (KeyError, ValueError):
            continue

    return results
