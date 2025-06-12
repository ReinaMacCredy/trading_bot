import httpx
from src.web.config.settings import settings

async def send_discord_message(content: str):
    async with httpx.AsyncClient() as client:
        await client.post(settings.DISCORD_WEBHOOK, json={"content": content})
