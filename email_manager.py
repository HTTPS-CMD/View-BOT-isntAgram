# import json
# import os
# from temp_mail import generate_1sec_email, get_1sec_messages


# def load_json(filepath):
#     if os.path.exists(filepath):
#         with open(filepath, "r") as f:
#             return json.load(f)
#     return []

# def save_json(filepath, data):
#     os.makedirs(os.path.dirname(filepath), exist_ok=True)
#     with open(filepath, "w") as f:
#         json.dump(data, f, indent=2)


# def is_email_active(email):
#     try:
#         messages = get_1sec_messages(email)
#         return messages is not None
#     except:
#         return False

# def load_active_emails(filepath="data/emails.json"):
#     emails = load_json(filepath)
#     active_emails = []

#     for e in emails:
#         # فرض کن ایمیل اگر جدید است (used=0) حتما فعال است بدون چک پیام
#         if e.get("active", True) and e.get("used", 0) < 5:
#             active_emails.append(e)
#         else:
#             e["active"] = False

#     save_json(filepath, emails)
#     return active_emails

#     for e in emails:
#         if e.get("active", True) and e.get("used", 0) < 5 and is_email_active(e["email"]):
#             active_emails.append(e)
#         else:
#             e["active"] = False

#     save_json(filepath, emails)
#     return active_emails

# def add_new_email(filepath="data/emails.json"):
#     emails = load_json(filepath)
#     new_email = {
#         "email": generate_1sec_email(),
#         "active": True,
#         "used": 0
#     }
#     emails.append(new_email)
#     save_json(filepath, emails)

#     print(f"Added new email: {new_email['email']}")  # پرینت ایمیل جدید
#     print(f"Total emails count: {len(emails)}")    # پرینت تعداد کل ایمیل‌ها

#     return new_email

# def mark_email_used(email_address, filepath="data/emails.json"):
#     """Increase usage count and deactivate if it reaches 5"""
#     emails = load_json(filepath)
#     for e in emails:
#         if e["email"] == email_address:
#             e["used"] = e.get("used", 0) + 1
#             if e["used"] >= 5:
#                 e["active"] = False
#     save_json(filepath, emails)