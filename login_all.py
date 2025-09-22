import json
import os
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

ACCOUNTS_FILE = "data/accounts.json"
COOKIES_DIR = "data/cookies"

# Ensure cookies directory exists
os.makedirs(COOKIES_DIR, exist_ok=True)

# Load all accounts
def load_accounts():
    with open(ACCOUNTS_FILE, "r") as f:
        return json.load(f)

# Save cookies for a specific account
def save_cookies(driver, username):
    with open(f"{COOKIES_DIR}/{username}.json", "w") as f:
        json.dump(driver.get_cookies(), f)

# Perform login for one account
def login_with_account(account):
    print(f"⏳ Logging in: {account['username']}")

    options = uc.ChromeOptions()
    options.add_argument("--no-first-run")
    options.add_argument("--no-service-autorun")
    options.add_argument("--password-store=basic")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")

    # Optional: attach proxy if available
    if account.get("proxy"):
        options.add_argument(f'--proxy-server={account["proxy"]}')

    driver = uc.Chrome(options=options)

    try:
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(random.uniform(3, 5))

        # Find username and password fields
        username_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")

        username_input.send_keys(account["username"])
        password_input.send_keys(account["password"])
        password_input.send_keys(Keys.ENTER)

        time.sleep(random.uniform(6, 9))  # Wait for login

        current_url = driver.current_url

        if "challenge" in current_url or "two_factor" in current_url:
            print(f"⚠️ Verification or 2FA required for: {account['username']}")
        elif "login" not in current_url:
            print(f"✅ Login successful: {account['username']}")
            save_cookies(driver, account["username"])
        else:
            print(f"❌ Login failed: {account['username']}")

    except Exception as e:
        print(f"❌ Error during login for {account['username']}: {e}")

    finally:
        driver.quit()

# Run login for all accounts
if __name__ == "__main__":
    accounts = load_accounts()
    for account in accounts:
        login_with_account(account)
        delay = random.uniform(5, 10)
        print(f"⏱️ Waiting {delay:.2f} seconds before next account...")
        time.sleep(delay)