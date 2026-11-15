import json

import httpx

from app.config import env
from app.platforms.base import Platform, PlatformError, PostOutcome, check

API = "https://api.telegra.ph"


class Telegraph(Platform):
    """Telegraph needs no sign-up: an anonymous account token is created on first use."""

    name = "Telegraph"
    _token: str = ""

    def is_configured(self) -> bool:
        return True

    async def _get_token(self, client: httpx.AsyncClient) -> str:
        if env("TELEGRAPH_ACCESS_TOKEN"):
            return env("TELEGRAPH_ACCESS_TOKEN")
        if not Telegraph._token:
            data = check(await client.post(f"{API}/createAccount", data={"short_name": "autoposter"}), "Telegraph account")
            if not data.get("ok"):
                raise PlatformError(f"Telegraph: {data.get('error', 'could not create account')}")
            Telegraph._token = data["result"]["access_token"]
        return Telegraph._token

    async def post(self, message: str, client: httpx.AsyncClient) -> PostOutcome:
        token = await self._get_token(client)
        title = message if len(message) <= 60 else message[:57] + "..."
        r = await client.post(
            f"{API}/createPage",
            data={
                "access_token": token,
                "title": title,
                "content": json.dumps([{"tag": "p", "children": [message]}]),
            },
        )
        data = check(r, "Telegraph")
        if not data.get("ok"):
            raise PlatformError(f"Telegraph: {data.get('error', 'unknown error')}")
        return PostOutcome(posted_url=data["result"]["url"])
