# import json
# import os
# import random
# import string
# import time
# import re
# import requests
# from loguru import logger

# BASE_URL = "https://api.mail.tm"


# # ---------- JSON HELPERS ----------
# def load_json(filepath):
#     if os.path.exists(filepath):
#         with open(filepath) as f:
#             content = f.read().strip()
#             if not content:
#                 return []
#             return json.loads(content)
#     return []


# def save_json(data, filepath):
#     os.makedirs(os.path.dirname(filepath), exist_ok=True)
#     with open(filepath, "w") as f:
#         json.dump(data, f, indent=2)
#     logger.success(f"[DEBUG] Saved {len(data)} items to {filepath}")


# # ---------- MAIL.TM HELPERS ----------
# def create_mailtm_account():
#     """ایجاد یک ایمیل جدید در Mail.tm و دریافت توکن"""
#     try:
#         domain_resp = requests.get(f"{BASE_URL}/domains", timeout=10)
#         domain_resp.raise_for_status()
#         domain = domain_resp.json()["hydra:member"][0]["domain"]

#         username = "user" + str(int(time.time()))
#         email = f"{username}@{domain}"
#         password = "Pass1234!"

#         data = {"address": email, "password": password}
#         resp = requests.post(f"{BASE_URL}/accounts", json=data)
#         if resp.status_code not in [200, 201]:
#             logger.error(f"❌ Account creation failed: {resp.text}")
#             return None

#         # دریافت توکن
#         token_resp = requests.post(f"{BASE_URL}/token", json=data)
#         token_resp.raise_for_status()
#         token = token_resp.json()["token"]

#         logger.success(f"✅ Created Mail.tm account: {email}")
#         return {"email": email, "password": password, "token": token, "active": True, "used": 0}

#     except Exception as e:
#         logger.error(f"❌ Mail.tm account creation error: {e}")
#         return None


# def get_messages(token):
#     headers = {"Authorization": f"Bearer {token}"}
#     resp = requests.get(f"{BASE_URL}/messages", headers=headers)
#     if resp.status_code != 200:
#         return []
#     return resp.json().get("hydra:member", [])


# def read_message(token, msg_id):
#     headers = {"Authorization": f"Bearer {token}"}
#     resp = requests.get(f"{BASE_URL}/messages/{msg_id}", headers=headers)
#     if resp.status_code != 200:
#         return {}
#     return resp.json()


# def extract_code(text):
#     match = re.search(r"\b\d{6}\b", text)
#     return match.group(0) if match else None


# def wait_for_code(token, timeout=180):
#     """دریافت کد تایید از Mail.tm"""
#     start = time.time()
#     while time.time() - start < timeout:
#         messages = get_messages(token)
#         if messages:
#             msg = messages[0]
#             logger.success(f"📩 Got message: {msg['subject']}")
#             content = read_message(token, msg["id"])
#             body = ""
#             if isinstance(content.get("text", ""), list):
#                 body += " ".join(content.get("text", []))
#             else:
#                 body += content.get("text", "")
#             body += content.get("html", "")
#             code = extract_code(body)
#             if code:
#                 logger.success(f"✅ Verification Code: {code}")
#                 return code
#         time.sleep(5)
#     logger.error("❌ Timeout waiting for verification code.")
#     return None


# # ---------- EMAIL MANAGEMENT ----------
# def is_email_active(email_entry):
#     """چک فعال بودن ایمیل Mail.tm"""
#     return email_entry.get("active", True) and email_entry.get("used", 0) < 5


# def load_active_emails(filepath="data/emails.json"):
#     emails = load_json(filepath)
#     active_emails = [e for e in emails if is_email_active(e)]
#     save_json(emails, filepath)
#     logger.success(f"[DEBUG] Loaded {len(active_emails)} active emails from {filepath}")
#     return active_emails


# def add_new_email(filepath="data/emails.json"):
#     emails = load_json(filepath)
#     new_email_entry = create_mailtm_account()
#     if not new_email_entry:
#         return None
#     emails.append(new_email_entry)
#     save_json(emails, filepath)
#     logger.success(f"[Email Manager] Added new Mail.tm email: {new_email_entry['email']}")
#     return new_email_entry


# def mark_email_used(email_address, filepath="data/emails.json"):
#     emails = load_json(filepath)
#     for e in emails:
#         if e["email"] == email_address:
#             e["used"] = e.get("used", 0) + 1
#             if e["used"] >= 5:
#                 e["active"] = False
#     save_json(emails, filepath)
#     logger.success(f"[Email Manager] Marked email used: {email_address}")


# # ---------- ACCOUNT GENERATION ----------
# def generate_username():
#     return "user_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


# def generate_password():
#     return "".join(random.choices(string.ascii_letters + string.digits, k=12))


# def create_fake_accounts(new_count=1, accounts_file="data/accounts.json", emails_file="data/emails.json"):
#     accounts = load_json(accounts_file)
#     active_emails = load_active_emails(emails_file)

#     while new_count > 0:
#         if not active_emails:
#             logger.warning("⚠️ No active email found. Creating a new Mail.tm email...")
#             new_email = add_new_email(emails_file)
#             if not new_email:
#                 logger.error("❌ Could not create new email. Aborting...")
#                 break
#             active_emails = [new_email]

#         email_entry = active_emails.pop(0)
#         mark_email_used(email_entry["email"], emails_file)

#         account = {
#             "username": generate_username(),
#             "password": generate_password(),
#             "email": email_entry["email"],
#             "token": email_entry.get("token")
#         }
#         accounts.append(account)
#         logger.success(f"[Account Manager] Created account: {account}")

#         # ✅ فقط اگر هنوز فعال باشد دوباره اضافه کن
#         if email_entry.get("used", 0) < 5 and email_entry.get("active", True):
#             active_emails.append(email_entry)

#         new_count -= 1

#     save_json(accounts, accounts_file)
#     logger.success(f"[Account Manager] Total accounts saved: {len(accounts)}")
#     return accounts


# # ---------- MAIN ----------
# if __name__ == "__main__":
#     new_count = int(input("How many new accounts do you want to add? "))
#     create_fake_accounts(new_count)

from instagram_bot import InstagramBot
from loguru import logger

if __name__ == "__main__":
    logger.success("🚀 Starting Instagram account creation...")
    bot = InstagramBot()
    bot.create_account()
