import random
import re
import string
import time

import requests
from loguru import logger

# Cloudflare Worker proxy
CLOUDFLARE_PROXY = "https://purple-wood-7c5f.m-gha5785.workers.dev/?url="
API_1SECMAIL = "https://www.1secmail.com/api/v1/"

def cf_request(url: str):
    """Send request through Cloudflare Worker proxy."""
    try:
        r = requests.get(CLOUDFLARE_PROXY + url, timeout=10)
        if r.status_code == 200 and r.text.strip():
            return r.json()
    except Exception as e:
        logger.error(f"{e}")
    else:
        return None

def direct_request(url: str):
    """Fallback request directly to API if proxy fails."""
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200 and r.text.strip():
            return r.json()
    except Exception as e:
        logger.error(f"{e}")
    else:
        return None

def safe_get_json(url: str):
    """Try Cloudflare first, fallback to direct request."""
    return cf_request(url) or direct_request(url) or []

def generate_1sec_email() -> str:
    """Generate a random temporary email from 1secmail."""
    user = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    domain = random.choice(["1secmail.com", "1secmail.net", "1secmail.org"])
    return f"{user}@{domain}"

def get_1sec_messages(email: str):
    """Fetch inbox messages for a given temp email."""
    login, domain = email.split("@")
    return safe_get_json(f"{API_1SECMAIL}?action=getMessages&login={login}&domain={domain}")

def read_1sec_message(email: str, msg_id: int):
    """Read a specific message by ID."""
    login, domain = email.split("@")
    return safe_get_json(f"{API_1SECMAIL}?action=readMessage&login={login}&domain={domain}&id={msg_id}")

def extract_verification_code(text: str):
    """Extract a 6-digit verification code from message text."""
    match = re.search(r"\b\d{6}\b", text)
    return match.group(0) if match else None

def wait_for_code(email: str, sender_filter="instagram.com", timeout=180):
    """Wait until a verification email arrives and extract the code.

    :param email: Temporary email address that will receive the verification code.
    :type email: str
    :param sender_filter: Expected sender's domain or email, defaults to "instagram.com".
    :type sender_filter: str, optional
    :param timeout: Maximum time (in seconds) the function will wait for the verification code, defaults to 180.
    :type timeout: int, optional
    :return: 6-digit verification code if found, otherwise None.
    :rtype: str or None
    """
    start = time.time()
    logger.success(f"Waiting for message from {sender_filter} for {email}...")

    while time.time() - start < timeout:
        messages = get_1sec_messages(email) or []
        for msg in messages:
            if sender_filter in msg.get("from", ""):
                logger.success(f"Message found: {msg['subject']}")
                content = read_1sec_message(email, msg["id"])
                code = extract_verification_code(content.get("body", ""))
                if code:
                    logger.success(f"Code: {code}")
                    return code
        time.sleep(5)

    logger.error("❌ No verification code received.")
    return None

if __name__ == "__main__":
    email = generate_1sec_email()
    logger.success(f"Temp email: {email}")
    code = wait_for_code(email)
    if code:
        logger.success(f"Final Code: {code}")
