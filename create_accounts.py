import json
import random
import string

# ساخت نام کاربری تصادفی
def generate_username():
    return 'user_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

# ساخت پسورد تصادفی
def generate_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

# ساخت ایمیل فیک برای هر اکانت (فرضی، واقعی نیست!)
def generate_email():
    domains = ['@example.com', '@tempmail.net', '@fakemail.org']
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10)) + random.choice(domains)

# ساخت لیست اکانت‌ها
def create_fake_accounts(count=10):
    accounts = []
    for _ in range(count):
        username = generate_username()
        password = generate_password()
        email = generate_email()
        accounts.append({
            "username": username,
            "password": password,
            "email": email
        })
    return accounts

# ذخیره در فایل
def save_accounts(accounts):
    with open("data/accounts.json", "w") as f:
        json.dump(accounts, f, indent=2)

if __name__ == "__main__":
    count = int(input("چند اکانت می‌خوای بسازم؟ "))
    accounts = create_fake_accounts(count)
    save_accounts(accounts)
    print(f"{count} اکانت در فایل data/accounts.json ذخیره شد.")
