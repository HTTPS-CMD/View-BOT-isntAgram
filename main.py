import os

from loguru import logger

from assign_proxies import assign_proxies_to_accounts
from create_accounts import create_fake_accounts, save_accounts
from login_all import load_accounts, login_with_account
from watch_video_parallel import main as watch_parallel

DATA_DIR = "data"
ACCOUNTS_FILE = os.path.join(DATA_DIR, "accounts.json")
COOKIES_DIR = os.path.join(DATA_DIR, "cookies")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(COOKIES_DIR, exist_ok=True)

def step_create_accounts():
    count = int(input("How many accounts you want to create?"))
    accounts = create_fake_accounts(count)
    save_accounts(accounts)
    logger.success(f"✅ {count} Account created and saved in {ACCOUNTS_FILE}.")

def step_assign_proxies():
    if not os.path.exists(ACCOUNTS_FILE):
        logger.error("Proxies file not found!")
        return
    assign_proxies_to_accounts(ACCOUNTS_FILE)
    logger.success("Proxies assigned successfully!")

def step_login_all():
    if not os.path.exists(ACCOUNTS_FILE):
        logger.error("Account's file not found!")
        return
    accounts = load_accounts()
    for acc in accounts:
        login_with_account(acc)
    logger.success("All accounts logged in successfully, coockies are saved")

def step_watch_videos_parallel():
    logger.warning("Proccess watching using multiple threads")
    watch_parallel()
    logger.success("Done watching videos")

if __name__ == "__main__":
    while True:
        logger.info("\n===== Instagram Automation Menu =====")
        logger.info("1. Create fake accounts")
        logger.info("2. Assign proxies")
        logger.info("3. Log-in all accounts and save cookies.")
        logger.info("4. Watch videos at tha same time ")
        logger.info("0. exit")

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
            logger.error("❌ گزینه نامعتبر.")
