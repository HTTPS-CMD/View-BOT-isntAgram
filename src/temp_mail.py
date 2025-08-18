import requests
import time
import re
import random
import string
from loguru import logger

BASE_URL = "https://api.mail.tm"

def create_mailtm_account():
    """ایجاد اکانت موقت Mail.tm و دریافت توکن JWT"""
    # دریافت دامین فعال
    domain_resp = requests.get(f"{BASE_URL}/domains")
    domain_resp.raise_for_status()
    domain = domain_resp.json()["hydra:member"][0]["domain"]

    # ساخت ایمیل و پسورد
    username = "user" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    email = f"{username}@{domain}"
    password = "Pass" + "".join(random.choices(string.ascii_letters + string.digits, k=6)) + "!"

    # ایجاد اکانت
    data = {"address": email, "password": password}
    resp = requests.post(f"{BASE_URL}/accounts", json=data)
    if resp.status_code not in [200, 201]:
        logger.error(f"❌ Account creation failed: {resp.text}")
        return None, None, None

    # گرفتن توکن
    token_resp = requests.post(f"{BASE_URL}/token", json=data)
    token_resp.raise_for_status()
    token = token_resp.json()["token"]

    logger.success(f"✅ Temporary Mail.tm account created: {email}")
    return email, password, token

def get_mailtm_messages(token):
    """دریافت لیست پیام‌های صندوق ورودی"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/messages", headers=headers)
    if resp.status_code != 200:
        logger.error(f"❌ Failed to fetch messages: {resp.text}")
        return []
    return resp.json().get("hydra:member", [])

def read_mailtm_message(token, msg_id):
    """خواندن محتوای پیام مشخص"""
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/messages/{msg_id}", headers=headers)
    if resp.status_code != 200:
        logger.error(f"❌ Failed to read message: {resp.text}")
        return {}
    return resp.json()

def extract_code(text):
    """استخراج کد 6 رقمی از متن"""
    match = re.search(r"\b\d{6}\b", text)
    return match.group(0) if match else None

def wait_for_mailtm_code(token, timeout=180):
    """منتظر دریافت کد تایید از اینستاگرام می‌ماند"""
    start = time.time()
    logger.info("⌛ Waiting for Instagram verification email...")

    while time.time() - start < timeout:
        messages = get_mailtm_messages(token)
        for msg in messages:
            if "instagram" in msg.get("from", {}).get("address", "").lower():
                logger.success(f"📩 Message received: {msg['subject']}")
                content = read_mailtm_message(token, msg["id"])
                
                # اصلاح: متن و HTML را بررسی و لیست‌ها را به string تبدیل می‌کنیم
                body = content.get("text", "")
                if isinstance(body, list):
                    body = "\n".join(body)

                html_content = content.get("html", "")
                if isinstance(html_content, list):
                    html_content = "".join(html_content)

                code = extract_code(body + html_content)
                if code:
                    logger.success(f"✅ Verification code: {code}")
                    return code
        time.sleep(5)

    logger.error("❌ No verification code received in time.")
    return None

# --- تست مستقیم ---
if __name__ == "__main__":
    email, password, token = create_mailtm_account()
    if not token:
        exit(1)

    print(f"Temporary Email: {email}")
    code = wait_for_mailtm_code(token)
    if code:
        print(f"Final Verification Code: {code}")
