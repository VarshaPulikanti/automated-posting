import httpx

from app.config import env
from app.platforms.base import Platform, PlatformError, PostOutcome, check


class Telegram(Platform):
    name = "Telegram"

    def is_configured(self) -> bool:
        return bool(env("TELEGRAM_BOT_TOKEN") and env("TELEGRAM_CHAT_ID"))

    async def post(self, message: str, client: httpx.AsyncClient) -> PostOutcome:
        r = await client.post(
            f"https://api.telegram.org/bot{env('TELEGRAM_BOT_TOKEN')}/sendMessage",
            json={"chat_id": env("TELEGRAM_CHAT_ID"), "text": message},
        )
        data = check(r, "Telegram")
        if not data.get("ok"):
            raise PlatformError(f"Telegram: {data.get('description', 'unknown error')}")
        result = data["result"]
        username = result["chat"].get("username")
        if not username:
            # Private channel: message exists but has no public link.
            return PostOutcome(posted_url=f"telegram://chat/{result['chat']['id']}/{result['message_id']}", public_access=False)
        return PostOutcome(posted_url=f"https://t.me/{username}/{result['message_id']}")
