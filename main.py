import asyncio
import os
import re
import aiohttp
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.getenv("TG_API_ID"))
API_HASH = os.getenv("TG_API_HASH")
SESSION_STR = os.getenv("TG_SESSION")

CHANNELS_FILE = "tg_channels.txt"
OUTPUT_FILE = "configs.txt"

# Регулярка для поиска RAW GitHub ссылок
RAW_GITHUB_REGEX = re.compile(
    r"https://raw\.githubusercontent\.com/[^\s]+\.txt"
)

# Регулярка для поиска конфигов
CONFIG_REGEX = re.compile(
    r"(vmess://[^\s]+|vless://[^\s]+|trojan://[^\s]+|ss://[^\s]+)"
)


def load_channels():
    channels = []
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                channels.append(line)
    return channels


async def download_raw(url: str) -> str:
    """Скачивает RAW-файл с GitHub"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    return await resp.text()
                else:
                    print(f"⚠ Ошибка загрузки RAW {url}: {resp.status}")
    except Exception as e:
        print(f"⚠ Ошибка RAW {url}: {e}")
    return ""


def extract_configs(text: str):
    """Извлекает все конфиги из текста"""
    return CONFIG_REGEX.findall(text)


async def scrape_once(client):
    channels = load_channels()
    all_configs = []

    for ch in channels:
        print(f"📡 Читаю канал: {ch}")

        async for msg in client.iter_messages(ch, limit=3000):
            if not msg.message:
                continue

            text = msg.message

            # 1. Ищем RAW GitHub ссылки
            raw_links = RAW_GITHUB_REGEX.findall(text)

            # 2. Скачиваем и парсим каждый RAW
            for link in raw_links:
                print(f"   → RAW найден: {link}")
                raw_text = await download_raw(link)

                cfgs = extract_configs(raw_text)
                all_configs.extend(cfgs)

            # 3. Также проверяем сам текст сообщения
            all_configs.extend(extract_configs(text))

    # Удаляем дубли
    all_configs = list(dict.fromkeys(all_configs))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for cfg in all_configs:
            f.write(cfg + "\n")

    print(f"💾 Сохранено {len(all_configs)} конфигов")


async def main():
    if not SESSION_STR:
        print("❌ TG_SESSION отсутствует")
        return

    client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("❌ Сессия недействительна")
        return

    await scrape_once(client)


if __name__ == "__main__":
    asyncio.run(main())
