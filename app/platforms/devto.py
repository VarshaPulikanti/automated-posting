import httpx

from app.config import env
from app.platforms.base import Platform, PlatformError, PostOutcome, check


class DevTo(Platform):
    name = "DEV Community"

    def is_configured(self) -> bool:
        return bool(env("DEVTO_API_KEY"))

    async def post(self, message: str, client: httpx.AsyncClient) -> PostOutcome:
        title = message if len(message) <= 80 else message[:77] + "..."
        r = await client.post(
            "https://dev.to/api/articles",
            headers={"api-key": env("DEVTO_API_KEY"), "Accept": "application/vnd.forem.api-v1+json"},
            json={"article": {"title": title, "body_markdown": message, "published": True}},
        )
        data = check(r, "DEV Community")
        if not data.get("url"):
            raise PlatformError("DEV Community: response did not contain an article URL")
        return PostOutcome(posted_url=data["url"], public_access=bool(data.get("published", True)))
