from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx


class PlatformError(Exception):
    """Readable, platform-level failure."""


@dataclass
class PostOutcome:
    posted_url: str
    public_access: bool = True


class Platform(ABC):
    name: str

    @abstractmethod
    def is_configured(self) -> bool:
        """True when all required credentials are present."""

    @abstractmethod
    async def post(self, message: str, client: httpx.AsyncClient) -> PostOutcome:
        """Publish the message. Raise PlatformError (or any exception) on failure."""


def check(response: httpx.Response, what: str) -> dict:
    """Turn HTTP errors into short readable messages and return the JSON body."""
    if response.status_code >= 400:
        snippet = response.text[:200].replace("\n", " ")
        if response.status_code in (401, 403):
            raise PlatformError(f"{what}: authentication failed (HTTP {response.status_code}) {snippet}")
        if response.status_code == 429:
            raise PlatformError(f"{what}: rate limited (HTTP 429)")
        raise PlatformError(f"{what}: HTTP {response.status_code} {snippet}")
    try:
        return response.json()
    except ValueError as exc:
        raise PlatformError(f"{what}: invalid JSON response") from exc
