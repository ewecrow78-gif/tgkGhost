import os
import asyncio
import requests
from telethon import TelegramClient
from config import API_ID, API_HASH, CHANNELS, OUTPUT_FILE, UPDATE_INTERVAL, normalize_channel
from parser import extract_all, normalize_config


async def scrape_once(client):
    all_configs = []
    norm_channels = [normalize_channel(c) for c in CHANNELS]

    for channel in norm_channels:
        print(f"[+] Читаю канал: {channel}")

        async for msg in client.iter_messages(channel, limit=500):
            if not msg.message:
                continue

            # Ищем только RAW-ссылки
            raw_links = [
                x for x in extract_all(msg.message)
                if x.startswith("https://raw")
            ]

            for raw in raw_links:
                print(f"  → Нашёл RAW: {raw}")
                try:
                    r = requests.get(raw, timeout=10)
                    r.raise_for_status()

                    raw_configs = extract_all(r.text)
                    all_configs.extend(raw_configs)

                except Exception as e:
                    print(f"Ошибка загрузки RAW: {e}")

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
    client = TelegramClient("session", API_ID, API_HASH)
    await client.start()

    while True:
        print("[⏳] Запуск обновления...")
        await scrape_once(client)

        print(f"[⏲] Следующее обновление через {UPDATE_INTERVAL // 60} минут.")
        await asyncio.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(run())
