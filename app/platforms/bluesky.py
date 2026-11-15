from datetime import datetime, timezone

import httpx

from app.config import env
from app.platforms.base import Platform, PlatformError, PostOutcome, check
from app.schemas import extract_urls

PDS = "https://bsky.social/xrpc"


class Bluesky(Platform):
    name = "Bluesky"

    def is_configured(self) -> bool:
        return bool(env("BLUESKY_HANDLE") and env("BLUESKY_APP_PASSWORD"))

    @staticmethod
    def _link_facets(message: str) -> list[dict]:
        """Bluesky needs explicit UTF-8 byte ranges to make links clickable."""
        facets = []
        raw = message.encode("utf-8")
        for url in extract_urls(message):
            encoded = url.encode("utf-8")
            start = raw.find(encoded)
            if start >= 0:
                facets.append({
                    "index": {"byteStart": start, "byteEnd": start + len(encoded)},
                    "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}],
                })
        return facets

    async def post(self, message: str, client: httpx.AsyncClient) -> PostOutcome:
        session = check(
            await client.post(
                f"{PDS}/com.atproto.server.createSession",
                json={"identifier": env("BLUESKY_HANDLE"), "password": env("BLUESKY_APP_PASSWORD")},
            ),
            "Bluesky login",
        )
        record = {
            "$type": "app.bsky.feed.post",
            "text": message,
            "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "facets": self._link_facets(message),
        }
        created = check(
            await client.post(
                f"{PDS}/com.atproto.repo.createRecord",
                headers={"Authorization": f"Bearer {session['accessJwt']}"},
                json={"repo": session["did"], "collection": "app.bsky.feed.post", "record": record},
            ),
            "Bluesky post",
        )
        uri = created.get("uri", "")  # at://did:plc:xxx/app.bsky.feed.post/<rkey>
        if not uri:
            raise PlatformError("Bluesky: response did not contain a post URI")
        rkey = uri.rsplit("/", 1)[-1]
        return PostOutcome(posted_url=f"https://bsky.app/profile/{session['handle']}/post/{rkey}")
