import os
import json
import random
import string
from temp_mail import generate_1sec_email, get_1sec_messages

# ----------- JSON Utils -----------
def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    return []

def save_json(data, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[DEBUG] Saved {len(data)} items to {filepath}")

# ----------- Email Management -----------
def is_email_active(email):
    try:
        messages = get_1sec_messages(email)
        return messages is not None
    except Exception as e:
        print(f"[DEBUG] Error checking email active status for {email}: {e}")
        return False

def load_active_emails(filepath="data/emails.json"):
    emails = load_json(filepath)
    active_emails = []
    for e in emails:
        if e.get("active", True) and e.get("used", 0) < 5:
            active_emails.append(e)
        else:
            e["active"] = False
    save_json(emails, filepath)
    print(f"[DEBUG] Loaded {len(active_emails)} active emails from {filepath}")
    return active_emails

def add_new_email(filepath="data/emails.json"):
    emails = load_json(filepath)
    new_email = {
        "email": generate_1sec_email(),
        "active": True,
        "used": 0
    }
    emails.append(new_email)
    save_json(emails, filepath)
    print(f"[Email Manager] Added new email: {new_email['email']}")
    return new_email

def mark_email_used(email_address, filepath="data/emails.json"):
    emails = load_json(filepath)
    for e in emails:
        if e["email"] == email_address:
            e["used"] = e.get("used", 0) + 1
            if e["used"] >= 5:
                e["active"] = False
    save_json(emails, filepath)
    print(f"[Email Manager] Marked email used: {email_address}")

# ----------- Account Management -----------
def generate_username():
    return 'user_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

def generate_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

def create_fake_accounts(new_count=1, accounts_file="data/accounts.json", emails_file="data/emails.json"):
    accounts = load_json(accounts_file)
    active_emails = load_active_emails(emails_file)

    while new_count > 0:
        if not active_emails:
            add_new_email(emails_file)
            active_emails = load_active_emails(emails_file)

        email_entry = active_emails.pop(0)
        mark_email_used(email_entry["email"], emails_file)

        account = {
            "username": generate_username(),
            "password": generate_password(),
            "email": email_entry["email"]
        }
        accounts.append(account)
        print(f"[Account Manager] Created account: {account}")

        # اگر ایمیل بعد از افزایش استفاده هنوز کمتر از ۵ بار استفاده شده، دوباره اضافه‌ش کن
        if email_entry.get("used", 0) < 5:
            active_emails.append(email_entry)

        new_count -= 1

    save_json(accounts, accounts_file)
    print(f"[Account Manager] Total accounts saved: {len(accounts)}")
    return accounts

# ----------- Main -----------
if __name__ == "__main__":
    new_count = int(input("How many new accounts do you want to add? "))
    create_fake_accounts(new_count)
