import os
import yaml

# Загружаем YAML-конфиг
with open("config.yml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

# API_ID и API_HASH берём из GitHub Secrets
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

# Каналы, файл вывода, интервал
CHANNELS = cfg["channels"]
OUTPUT_FILE = cfg["output"]["file"]
UPDATE_INTERVAL = cfg["update"]["interval_minutes"] * 60  # в секундах


def normalize_channel(ch: str) -> str:
    """
    Приводит канал к формату https://t.me/...
    """
    ch = ch.strip()

    if ch.startswith("https://t.me/"):
        return ch

    if ch.startswith("@"):
        return "https://t.me/" + ch[1:]

    return "https://t.me/" + ch
