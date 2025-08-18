import json
import os
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.safari.service import Service as SafariService
from selenium.common.exceptions import WebDriverException

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


    # Initialize Safari WebDriver
    driver = webdriver.Safari()

    try:
        driver.get("https://www.instagram.com/accounts/login/")
        el = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//*[text()='Allow all cookies']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", el)
        el.click()
        time.sleep(random.uniform(3, 5))

        # Find username and password fields using WebDriverWait
        username_input = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.NAME, "username"))
        )
        password_input = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.NAME, "password"))
        )

        # Debug checks to ensure we located distinct elements
        try:
            print(f"DEBUG: username element name={username_input.get_attribute('name')}, password element name={password_input.get_attribute('name')}")
        except Exception:
            print("DEBUG: unable to read element attributes")

        if username_input == password_input or (username_input.get_attribute('name') == password_input.get_attribute('name')):
            print("⚠️ Warning: username and password elements look identical. Trying alternative selectors.")
            try:
                username_input = driver.find_element(By.CSS_SELECTOR, "input[name='username']")
                password_input = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
                print("DEBUG: Re-located inputs via CSS selector.")
            except Exception as e:
                print("❌ Could not re-locate distinct input fields:", e)

        # Focus, clear and type slowly (char-by-char) to avoid focus-stealing issues
        try:
            username_input.click()
            username_input.clear()
        except Exception:
            pass
        for ch in account["username"]:
            username_input.send_keys(ch)
            time.sleep(random.uniform(0.03, 0.08))

        time.sleep(random.uniform(0.2, 0.5))

        try:
            password_input.click()
            password_input.clear()
        except Exception:
            pass
        for ch in account["password"]:
            password_input.send_keys(ch)
            time.sleep(random.uniform(0.03, 0.08))

        password_input.send_keys(Keys.ENTER)
        time.sleep(7)  # wait for page to load after login attempt
        print(driver.page_source)  # print page source to debug potential errors like captcha or message

        # Wait until we leave the login page or a challenge/2FA page appears
        try:
            WebDriverWait(driver, 10).until(lambda d: "login" not in d.current_url or "challenge" in d.current_url or "two_factor" in d.current_url)
        except Exception:
            pass

        time.sleep(random.uniform(6, 9))  # Wait for login

        current_url = driver.current_url

        if "challenge" in current_url or "two_factor" in current_url:
            print(f"⚠️ Verification or 2FA required for: {account['username']}")
            print("⏳ Waiting for manual verification... Please complete the challenge/2FA in the opened browser window.")
            try:
                WebDriverWait(driver, 300).until(
                    lambda d: "instagram.com" in d.current_url and "login" not in d.current_url
                )
                print("✅ Verification complete.")
                save_cookies(driver, account["username"])
            except Exception:
                print("❌ Timeout waiting for verification.")
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
