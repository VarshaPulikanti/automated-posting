import httpx

from app.config import env
from app.platforms.base import Platform, PlatformError, PostOutcome, check


class Mastodon(Platform):
    name = "Mastodon"

    def is_configured(self) -> bool:
        return bool(env("MASTODON_INSTANCE_URL") and env("MASTODON_ACCESS_TOKEN"))

    async def post(self, message: str, client: httpx.AsyncClient) -> PostOutcome:
        base = env("MASTODON_INSTANCE_URL").rstrip("/")
        r = await client.post(
            f"{base}/api/v1/statuses",
            headers={"Authorization": f"Bearer {env('MASTODON_ACCESS_TOKEN')}"},
            data={"status": message, "visibility": "public"},
        )
        data = check(r, "Mastodon")
        if not data.get("url"):
            raise PlatformError("Mastodon: response did not contain a post URL")
        return PostOutcome(posted_url=data["url"], public_access=data.get("visibility") == "public")
