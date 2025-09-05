

import requests
import random
import string
import time
import re
from loguru import logger

BASE = "https://api.mail.tm"

def _rand(n=8):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))

def create_mailtm_account():
    # دریافت دامنه‌ی temp
    resp = requests.get(f"{BASE}/domains")
    data = resp.json()
    domain = data["hydra:member"][0]["domain"]
    username = _rand(10)
    password = _rand(12)
    address = f"{username}@{domain}"

    acc = {"address": address, "password": password}
    res = requests.post(f"{BASE}/accounts", json=acc)
    if res.status_code != 201:
        logger.error("❌ Account creation failed! " + res.text)
        return None, None, None

    auth = requests.post(f"{BASE}/token", json=acc)
    if auth.status_code != 200:
        logger.error("❌ Login failed! " + auth.text)
        return None, None, None

    token = auth.json()["token"]
    logger.success(f"✅ mail.tm inbox ready: {address}")
    return address, password, token

def wait_for_mailtm_code(token, timeout=180, poll_interval=6):
    headers = {"Authorization": f"Bearer {token}"}
    start = time.time()
    logger.info("⌛ Waiting for Instagram verification email (mail.tm)...")
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{BASE}/messages", headers=headers)
            for msg in resp.json()["hydra:member"]:
                sub = msg.get("subject", "").lower()
                frm = msg.get("from", {}).get("address", "").lower()
                if "instagram" in frm or "instagram" in sub or "code" in sub:
                    message_id = msg["id"]
                    msg_resp = requests.get(f"{BASE}/messages/{message_id}", headers=headers)
                    body = msg_resp.json().get("text", "") + '\n' + msg_resp.json().get("subject", "")
                    code_match = re.search(r"(\d{6})", body)
                    if code_match:
                        code = code_match.group(1)
                        logger.success(f"✅ Verification code: {code}")
                        return code
        except Exception as e:
            logger.warning(f"Waiting error: {e}")
        time.sleep(poll_interval)
    logger.error("❌ No verification code received in time.")
    return None

# test mode
if __name__ == "__main__":
    email, password, token = create_mailgw_account()
    print("Email:", email)
    code = wait_for_mailgw_code(email, token)
    print("Code:", code)
