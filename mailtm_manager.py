# mailtm_manager.py
import json
import os
import random
import string
import time
import re
import requests
from loguru import logger

BASE_URL = "https://api.mail.tm"

# ---------- JSON HELPERS ----------
def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath) as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    return []

def save_json(data, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    logger.success(f"[DEBUG] Saved {len(data)} items to {filepath}")

# ---------- MAIL.TM HELPERS ----------
def create_mailtm_account():
    try:
        domain_resp = requests.get(f"{BASE_URL}/domains", timeout=10)
        domain_resp.raise_for_status()
        domain = domain_resp.json()["hydra:member"][0]["domain"]

        username = "user" + str(int(time.time()))
        email = f"{username}@{domain}"
        password = "Pass1234!"
        data = {"address": email, "password": password}

        resp = requests.post(f"{BASE_URL}/accounts", json=data)
        if resp.status_code not in [200, 201]:
            logger.error(f"❌ Account creation failed: {resp.text}")
            return None

        token_resp = requests.post(f"{BASE_URL}/token", json=data)
        token_resp.raise_for_status()
        token = token_resp.json()["token"]

        return {"email": email, "password": password, "token": token, "active": True, "used": 0}

    except Exception as e:
        logger.error(f"❌ Mail.tm error: {e}")
        return None

def get_messages(token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/messages", headers=headers)
    return resp.json().get("hydra:member", []) if resp.status_code == 200 else []

def read_message(token, msg_id):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/messages/{msg_id}", headers=headers)
    return resp.json() if resp.status_code == 200 else {}

def extract_code(text):
    match = re.search(r"\b\d{6}\b", text)
    return match.group(0) if match else None

def wait_for_code(token, timeout=180):
    start = time.time()
    while time.time() - start < timeout:
        messages = get_messages(token)
        if messages:
            msg = messages[0]
            content = read_message(token, msg["id"])
            body = (content.get("text", "") if not isinstance(content.get("text", ""), list) 
                    else " ".join(content.get("text", []))) + content.get("html", "")
            code = extract_code(body)
            if code:
                logger.success(f"✅ Verification Code: {code}")
                return code
        time.sleep(5)
    logger.error("❌ Timeout waiting for code.")
    return None

# ---------- EMAIL MANAGEMENT ----------
def is_email_active(email_entry):
    return email_entry.get("active", True) and email_entry.get("used", 0) < 5

def load_active_emails(filepath="data/emails.json"):
    emails = load_json(filepath)
    active = [e for e in emails if is_email_active(e)]
    save_json(emails, filepath)
    return active

def add_new_email(filepath="data/emails.json"):
    emails = load_json(filepath)
    new_email = create_mailtm_account()
    if not new_email: return None
    emails.append(new_email)
    save_json(emails, filepath)
    return new_email

def mark_email_used(email_address, filepath="data/emails.json"):
    emails = load_json(filepath)
    for e in emails:
        if e["email"] == email_address:
            e["used"] += 1
            if e["used"] >= 5: e["active"] = False
    save_json(emails, filepath)
