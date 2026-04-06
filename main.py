import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession

from parser import extract_all, normalize_config
from config import CHANNELS, OUTPUT_FILE, UPDATE_INTERVAL, normalize_channel


API_ID = int(os.getenv("TG_API_ID"))
API_HASH = os.getenv("TG_API_HASH")
SESSION_STR = os.getenv("TG_SESSION")


async def scrape_once(client):
    all_configs = []
    norm_channels = [normalize_channel(c) for c in CHANNELS]

    for channel in norm_channels:
        print(f"[+] Читаю канал: {channel}")

        async for msg in client.iter_messages(channel, limit=500):
            if not msg.message:
                continue

            configs = extract_all(msg.message)
            all_configs.extend(configs)

    # нормализация + удаление дублей
    normalized = {normalize_config(cfg): cfg for cfg in all_configs}
    final_list = list(normalized.keys())

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for cfg in final_list:
            f.write(cfg + "\n")

    print(f"[✓] Готово! Уникальных конфигов: {len(final_list)}")
    print(f"Сохранено в {OUTPUT_FILE}")
    print("-" * 40)


async def run():
    if not SESSION_STR:
        print("❌ TG_SESSION отсутствует в Secrets")
        return

    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("❌ TG_SESSION недействителен — обнови секрет")
        return

    while True:
        print("[⏳] Запуск обновления...")
        await scrape_once(client)

        print(f"[⏲] Следующее обновление через {UPDATE_INTERVAL // 60} минут.")
        await asyncio.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(run())
