import re
from typing import Literal, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator

MAX_LENGTH = 200
URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
HOST_PATTERN = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$", re.IGNORECASE)


def extract_urls(message: str) -> list[str]:
    """Find http(s) links, trimming trailing sentence punctuation."""
    return [m.rstrip(".,;:!?)\"'") for m in URL_PATTERN.findall(message)]


def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.hostname) and bool(HOST_PATTERN.match(parsed.hostname))


class PostingRequest(BaseModel):
    message: str = Field(..., examples=["Check out our latest business platform. https://example.com"])

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message must not be empty.")
        if len(value) > MAX_LENGTH:
            raise ValueError(f"Message must not exceed {MAX_LENGTH} characters (got {len(value)}).")
        urls = extract_urls(value)
        if len(urls) != 1:
            raise ValueError(f"Message must contain exactly one CTA link (found {len(urls)}).")
        if not is_valid_url(urls[0]):
            raise ValueError(f"The CTA link is not a valid URL: {urls[0]}")
        return value


class PlatformResult(BaseModel):
    platform: str
    status: Literal["success", "failed"]
    posted_url: Optional[str] = None
    public_access: bool = False
    date: Optional[str] = None
    time: Optional[str] = None
    error: Optional[str] = None


class PostingResponse(BaseModel):
    success: bool
    results: list[PlatformResult]
