import asyncio
import os
import re
import aiohttp
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import RPCError

# Конфигурация из переменных окружения
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
    """Загружает список каналов из файла, очищая их от лишних символов"""
    channels = []
    if not os.path.exists(CHANNELS_FILE):
        print(f"⚠ Файл {CHANNELS_FILE} не найден.")
        return []
    
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Убираем @ в начале и лишние пробелы, если они есть
            if line and not line.startswith("#"):
                clean_ch = line.lstrip('@')
                channels.append(clean_ch)
    return channels

async def download_raw(url: str) -> str:
    """Скачивает RAW-файл с GitHub"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    return await resp.text()
                else:
                    print(f"  ⚠ Ошибка загрузки RAW {url}: {resp.status}")
    except Exception as e:
        print(f"  ⚠ Ошибка при скачивании RAW {url}: {e}")
    return ""

def extract_configs(text: str):
    """Извлекает все конфиги из текста"""
    if not text:
        return []
    return CONFIG_REGEX.findall(text)

async def scrape_once(client):
    channels = load_channels()
    all_configs = []
    
    print(f"🚀 Начинаю сбор данных из {len(channels)} источников...")

    for ch in channels:
        print(f"📡 Читаю канал: {ch}")
        try:
            # Оборачиваем чтение конкретного канала в try-except
            async for msg in client.iter_messages(ch, limit=1800):
                if not msg or not msg.message:
                    continue
                
                text = msg.message
                
                # 1. Ищем RAW GitHub ссылки в тексте сообщения
                raw_links = RAW_GITHUB_REGEX.findall(text)
                for link in raw_links:
                    print(f"  → RAW найден: {link}")
                    raw_text = await download_raw(link)
                    cfgs = extract_configs(raw_text)
                    all_configs.extend(cfgs)

                # 2. Также проверяем сам текст сообщения на наличие конфигов
                all_configs.extend(extract_configs(text))
                
        except ValueError:
            print(f"  ❌ Ошибка: Канал '{ch}' не найден (возможно, удален или опечатка).")
        except RPCError as e:
            print(f"  ❌ Ошибка Telegram API для {ch}: {e}")
        except Exception as e:
            print(f"  ❌ Непредвиденная ошибка при чтении {ch}: {e}")

    # Удаляем дубликаты
    initial_count = len(all_configs)
    all_configs = list(dict.fromkeys(all_configs))
    print(f"✨ Сбор окончен. Найдено всего: {initial_count}, уникальных: {len(all_configs)}")

    # Сохраняем результат
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            for cfg in all_configs:
                f.write(cfg + "\n")
        print(f"💾 Результаты сохранены в {OUTPUT_FILE}")
    except Exception as e:
        print(f"❌ Ошибка при сохранении файла: {e}")

async def main():
    if not SESSION_STR:
        print("❌ Ошибка: Переменная окружения TG_SESSION не задана.")
        return
    
    try:
        client = TelegramClient(StringSession(SESSION_STR), API_ID, API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            print("❌ Ошибка: Сессия неавторизована. Проверьте TG_SESSION.")
            return

        await scrape_once(client)
        
    except Exception as e:
        print(f"❌ Критическая ошибка в main: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
