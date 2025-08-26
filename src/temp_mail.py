# temp_mail.py
import time
import re
import random
import string
from loguru import logger

import cloudscraper  # pip install cloudscraper

MAILDROP_BASE = "https://maildrop.cc/api"

# یک اسکرِیپر جهانی با سشن پایدار
_scraper = cloudscraper.create_scraper(
    browser={
        "browser": "chrome",
        "platform": "windows",
        "mobile": False,
    },
    delay=10,  # تاخیر برای چالش‌های CF اگر نیاز باشد
)

def _rand_str(n=8, alphabet=None):
    import secrets
    if alphabet is None:
        alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))

def _ensure_text(x):
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if isinstance(x, list):
        return "\n".join(_ensure_text(i) for i in x)
    if isinstance(x, dict):
        parts = []
        for k in ("address", "name", "email", "subject"):
            if k in x and x[k]:
                parts.append(str(x[k]))
        if not parts:
            parts = [str(v) for v in x.values() if v is not None]
        return "\n".join(parts)
    return str(x)

def extract_code(text):
    if not text:
        return None
    patterns = [
        r"(?:instagram[^.\n]{0,40})?(?:confirmation|security)?\s*code[^\d]{0,20}(\d{6})",
        r"(?:your\s+code\s+is[^\d]{0,20})(\d{6})",
        r"(?<!\d)(\d{6})(?!\d)",
    ]
    low = text.lower()
    for pat in patterns:
        m = re.search(pat, low, flags=re.IGNORECASE)
        if m:
            return m.group(1) if m.lastindex else m.group(0)
    return None

def _md_local_from_email(email: str) -> str:
    return email.split("@", 1)[0]

def _md_get_messages(local: str):
    url = f"{MAILDROP_BASE}/inbox/{local}"
    try:
        resp = _scraper.get(url, timeout=20)
        if resp.status_code != 200:
            logger.error(f"❌ Maildrop inbox fetch failed {resp.status_code}: {resp.text[:200]}")
            return []
        data = resp.json() or {}
        messages = data.get("messages") or []
        normalized = []
        for m in messages:
            normalized.append({
                "id": m.get("id"),
                "subject": m.get("subject", ""),
                "from": {"address": m.get("from", "")},
                "createdAt": 0,
            })
        return normalized
    except Exception as e:
        logger.error(f"❌ Maildrop get messages error: {e}")
        return []

def _md_read_message(local: str, msg_id: str):
    url = f"{MAILDROP_BASE}/message/{local}/{msg_id}"
    try:
        resp = _scraper.get(url, timeout=20)
        if resp.status_code != 200:
            logger.error(f"❌ Maildrop read message failed {resp.status_code}: {resp.text[:200]}")
            return {}
        data = resp.json() or {}
        return {
            "subject": data.get("subject", ""),
            "text": data.get("body", "") or "",
            "html": "",
            "from": {"address": data.get("from", "")},
        }
    except Exception as e:
        logger.error(f"❌ Maildrop read message error: {e}")
        return {}

# Public API (names preserved)
def create_mailtm_account():
    local = "user" + _rand_str(10)
    email = f"{local}@maildrop.cc"
    password = _rand_str(12)
    token = {"provider": "maildrop", "email": email, "local": local}
    logger.success(f"✅ Maildrop inbox ready: {email}")
    return email, password, token

def get_mailtm_messages(token):
    if not isinstance(token, dict) or token.get("provider") != "maildrop":
        logger.error("❌ Invalid token: expected dict with provider='maildrop'")
        return []
    return _md_get_messages(token["local"])

def read_mailtm_message(token, msg_id):
    if not isinstance(token, dict) or token.get("provider") != "maildrop":
        logger.error("❌ Invalid token: expected dict with provider='maildrop'")
        return {}
    return _md_read_message(token["local"], msg_id)

def wait_for_mailtm_code(token, max_retries=3, timeout=180, poll_interval=3, not_before_ts=None):
    if not isinstance(token, dict) or token.get("provider") != "maildrop":
        logger.error("❌ Invalid token: expected dict with provider='maildrop'")
        return None

    start = time.time()
    seen_ids = set()
    logger.info("⌛ Waiting for verification email (Maildrop)…")

    while time.time() - start < timeout:
        msgs = get_mailtm_messages(token)
        if not isinstance(msgs, list):
            time.sleep(poll_interval)
            continue

        def is_instagram(m):
            subj = _ensure_text(m.get("subject", "")).lower()
            frm = _ensure_text((m.get("from") or {}).get("address", "")).lower()
            return ("instagram" in subj) or ("instagram" in frm) or ("code" in subj)

        candidates = [m for m in msgs if is_instagram(m)] or msgs

        for m in candidates:
            mid = m.get("id")
            if not mid or mid in seen_ids:
                continue

            content = read_mailtm_message(token, mid)
            subj = _ensure_text(content.get("subject") or m.get("subject") or "")
            body = _ensure_text(content.get("text") or "")
            combined = "\n".join(filter(None, [subj, body]))
            code = extract_code(combined)
            seen_ids.add(mid)

            if code:
                logger.success(f"📩 Verification code received: {code}")
                return code

        time.sleep(max(2, poll_interval))

    logger.error("❌ No valid verification code received in time.")
    return None

if __name__ == "__main__":
    email, password, token = create_mailtm_account()
    print("Email (Maildrop):", email)
    code = wait_for_mailtm_code(token, timeout=180, poll_interval=3)
    print("Code:", code)
