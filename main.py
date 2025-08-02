import os
import json
from create_account import create_fake_accounts, save_accounts
from login_all import load_accounts, login_with_account
from watch_video_parallel import main as watch_parallel
from assign_proxies import assign_proxies_to_accounts

DATA_DIR = "data"
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")
COOKIES_DIR = os.path.join(DATA_DIR, "cookies")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(COOKIES_DIR, exist_ok=True)

def step_create_accounts():
    count = int(input("🔹 چند اکانت می‌خوای بسازم؟ "))
    accounts = create_fake_accounts(count)
    save_accounts(accounts)
    print(f"✅ {count} اکانت ساخته شد و در {ACCOUNTS_FILE} ذخیره شد.")

def step_assign_proxies():
    if not os.path.exists(ACCOUNTS_FILE):
        print("❌ فایل اکانت‌ها موجود نیست.")
        return
    assign_proxies_to_accounts(ACCOUNTS_FILE)
    print("✅ پروکسی‌ها به اکانت‌ها اختصاص داده شد.")

def step_login_all():
    if not os.path.exists(ACCOUNTS_FILE):
        print("❌ فایل اکانت‌ها موجود نیست.")
        return
    accounts = load_accounts()
    for acc in accounts:
        login_with_account(acc)
    print("✅ لاگین همه اکانت‌ها انجام شد و کوکی‌ها ذخیره شدند.")

def step_watch_videos_parallel():
    print("▶️ شروع تماشای ویدیوها به صورت موازی...")
    watch_parallel()
    print("✅ عملیات تماشای ویدیوها تمام شد.")

if __name__ == "__main__":
    while True:
        print("\n===== Instagram Automation Menu =====")
        print("1. ساخت اکانت‌های فیک")
        print("2. اختصاص پروکسی به اکانت‌ها")
        print("3. لاگین همه اکانت‌ها و ذخیره کوکی")
        print("4. تماشای ویدیوها به صورت موازی")
        print("0. خروج")
        
        choice = input("انتخاب شما: ")

        if choice == "1":
            step_create_accounts()
        elif choice == "2":
            step_assign_proxies()
        elif choice == "3":
            step_login_all()
        elif choice == "4":
            step_watch_videos_parallel()
        elif choice == "0":
            break
        else:
            print("❌ گزینه نامعتبر.")