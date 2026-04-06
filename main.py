import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.getenv("TG_API_ID"))
API_HASH = os.getenv("TG_API_HASH")
SESSION_STR = os.getenv("TG_SESSION")

CHANNELS_FILE = "tg_channels.txt"
OUTPUT_FILE = "configs.txt"


def load_channels():
    channels = []
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                channels.append(line)
    return channels


async def safe_iter_messages(client, channel, limit):
    try:
        async with asyncio.timeout(15):  # максимум 15 секунд на канал
            async for msg in client.iter_messages(channel, limit=limit):
                yield msg
    except asyncio.TimeoutError:
        print(f"⚠ Таймаут при чтении канала: {channel}")


async def scrape_once(client):
    channels = load_channels()
    all_cfg = []

    for ch in channels:
        print(f"Читаю канал: {ch}")
        async for msg in safe_iter_messages(client, ch, limit=600):
            if msg.message:
                for line in msg.message.split("\n"):
                    line = line.strip()
                    if line.startswith(("vmess://", "vless://", "trojan://", "ss://")):
                        all_cfg.append(line)

    # удаляем дубли
    all_cfg = list(dict.fromkeys(all_cfg))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for cfg in all_cfg:
            f.write(cfg + "\n")

    print(f"Сохранено {len(all_cfg)} конфигов")


async def main():
    if not SESSION_STR:
        print("❌ TG_SESSION отсутствует")
        return

    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("❌ Сессия недействительна")
        return

    await scrape_once(client)  # ← один запуск и выход


if __name__ == "__main__":
    asyncio.run(main())
