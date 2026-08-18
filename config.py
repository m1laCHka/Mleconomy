import os
from dataclasses import dataclass

@dataclass
class Config:
    bot_token: str
    admin_id: int
    database_url: str
    chat_id: int | None = None
    port: int = 8080

config = Config(
    bot_token=os.getenv("BOT_TOKEN", ""),
    admin_id=int(os.getenv("ADMIN_ID", "0")),
    database_url=os.getenv("DATABASE_URL", ""),
    chat_id=int(os.getenv("CHAT_ID")) if os.getenv("CHAT_ID") else None,
    port=int(os.getenv("PORT", "8080")),
)
