from app.platforms.base import Platform
from app.platforms.bluesky import Bluesky
from app.platforms.devto import DevTo
from app.platforms.mastodon import Mastodon
from app.platforms.telegram import Telegram
from app.platforms.telegraph import Telegraph


def get_platforms() -> list[Platform]:
    """Platform selection is handled internally; add a class here to add a platform."""
    return [Mastodon(), Bluesky(), Telegram(), DevTo(), Telegraph()]
