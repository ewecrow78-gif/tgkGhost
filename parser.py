import re
import base64
import json
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

PATTERNS = {
    "vless": r"(vless://[^\s]+)",
    "vmess": r"(vmess://[^\s]+)",
    "trojan": r"(trojan://[^\s]+)",
    "ss": r"(ss://[^\s]+)",
    "ssr": r"(ssr://[^\s]+)",
    "hysteria": r"(hysteria2?://[^\s]+)",
    "raw": r"(https://raw\.githubusercontent\.com/[^\s]+)"
}

def extract_all(text: str):
    results = []
    for name, pattern in PATTERNS.items():
        matches = re.findall(pattern, text)
        results.extend(matches)
    return results


def normalize_vmess(link: str):
    try:
        raw = link.replace("vmess://", "")
        decoded = base64.urlsafe_b64decode(raw + "==").decode()
        data = json.loads(decoded)
        data = dict(sorted(data.items()))
        new_raw = json.dumps(data, separators=(",", ":"))
        new_encoded = base64.urlsafe_b64encode(new_raw.encode()).decode()
        return "vmess://" + new_encoded
    except:
        return link.strip()


def normalize_url(link: str):
    try:
        parsed = urlparse(link)
        query = sorted(parse_qsl(parsed.query))
        new_query = urlencode(query)
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
        return normalized.strip()
    except:
        return link.strip()


def normalize_config(link: str):
    link = link.strip()

    if link.startswith("vmess://"):
        return normalize_vmess(link)

    if link.startswith(("vless://", "trojan://", "ss://", "hysteria://", "hysteria2://")):
        return normalize_url(link)

    return link
