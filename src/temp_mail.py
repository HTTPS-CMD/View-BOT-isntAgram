import requests
import time
import re
import random
import string
from loguru import logger

BASE_URL = "https://www.1secmail.com/api/v1/"

def create_mailtm_account():
    """ایجاد ایمیل موقت با 1secmail و دریافت اطلاعات"""
    username = "user" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    domain = random.choice(["1secmail.com", "1secmail.net", "1secmail.org"])
    email = f"{username}@{domain}"
    password = "".join(random.choices(string.ascii_letters + string.digits, k=12))  # صرفاً placeholder

    logger.success(f"✅ Temporary 1secmail account created: {email}")
    token = (username, domain)  # برای 1secmail، token همان username+domain است
    return email, password, token

def get_mailtm_messages(token):
    """لیست پیام‌ها را دریافت می‌کند"""
    username, domain = token
    params = {"action": "getMessages", "login": username, "domain": domain}
    resp = requests.get(BASE_URL, params=params)
    if resp.status_code != 200:
        logger.error(f"❌ Failed to fetch messages: {resp.text}")
        return []
    return resp.json()

def read_mailtm_message(token, msg_id):
    """خواندن محتوای پیام مشخص"""
    username, domain = token
    params = {"action": "readMessage", "login": username, "domain": domain, "id": msg_id}
    resp = requests.get(BASE_URL, params=params)
    if resp.status_code != 200:
        logger.error(f"❌ Failed to read message: {resp.text}")
        return {}
    return resp.json()

def extract_code(text):
    """استخراج کد 6 رقمی از متن"""
    if not text:
        return None
    match = re.search(r"\b\d{6}\b", text)
    return match.group(0) if match else None

def wait_for_mailtm_code(token, max_retries=3, timeout=180):
    """
    دریافت کد اینستاگرام و نمایش در ترمینال.
    کاربر خودش کد را وارد می‌کند.
    """
    start = time.time()
    logger.info("⌛ Waiting for Instagram verification email...")

    last_checked_id = None

    while time.time() - start < timeout:
        messages = get_mailtm_messages(token)
        instagram_msgs = [
            m for m in messages if "instagram" in m.get("from", "").lower()
        ]
        if not instagram_msgs:
            time.sleep(3)
            continue

        latest_msg = instagram_msgs[0]
        if latest_msg["id"] == last_checked_id:
            time.sleep(2)
            continue
        last_checked_id = latest_msg["id"]

        content = read_mailtm_message(token, latest_msg["id"])
        body = content.get("textBody", "")
        html = content.get("htmlBody", "")

        combined_text = (body or "") + (html or "")
        code = extract_code(combined_text)

        if code:
            logger.success(f"📩 Verification code received: {code}")
            print(f"\n💡 Instagram verification code: {code}")
            input("➡️ Enter the code manually in Instagram and press Enter here to continue...")
            return code

        time.sleep(3)

    logger.error("❌ No valid Instagram verification code received in time.")
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
