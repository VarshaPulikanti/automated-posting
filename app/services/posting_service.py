import asyncio
import logging
from datetime import datetime, timezone

import httpx

from app.platforms import get_platforms
from app.platforms.base import Platform, PlatformError
from app.schemas import PlatformResult, PostingResponse

logger = logging.getLogger("posting")


async def _post_one(platform: Platform, message: str, client: httpx.AsyncClient) -> PlatformResult:
    """Isolated per platform: any error becomes a 'failed' result, never an exception."""
    try:
        if not platform.is_configured():
            raise PlatformError("Credentials not configured (see .env.example)")
        outcome = await platform.post(message, client)
        now = datetime.now(timezone.utc)
        logger.info("%s: posted %s", platform.name, outcome.posted_url)
        return PlatformResult(
            platform=platform.name,
            status="success",
            posted_url=outcome.posted_url,
            public_access=outcome.public_access,
            date=now.strftime("%Y-%m-%d"),
            time=now.strftime("%H:%M:%S"),
        )
    except httpx.TimeoutException:
        error = "Request timed out"
    except httpx.HTTPError as exc:
        error = f"Network error: {exc.__class__.__name__}"
    except PlatformError as exc:
        error = str(exc)
    except Exception as exc:  # noqa: BLE001 - one platform must never break the others
        logger.exception("%s: unexpected error", platform.name)
        error = f"Unexpected error: {exc.__class__.__name__}"
    logger.warning("%s: failed - %s", platform.name, error)
    return PlatformResult(platform=platform.name, status="failed", error=error)


async def publish(message: str, platforms: list[Platform] | None = None) -> PostingResponse:
    platforms = platforms if platforms is not None else get_platforms()
    async with httpx.AsyncClient(timeout=15.0) as client:
        results = await asyncio.gather(*(_post_one(p, message, client) for p in platforms))
    return PostingResponse(success=any(r.status == "success" for r in results), results=list(results))
