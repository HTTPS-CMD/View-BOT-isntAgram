# main.py (English logs - using mail.tm)

import random
import string
from time import sleep

from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from temp_mail import create_mailtm_account, wait_for_mailtm_code

NAMES = [
    "Alice Johnson", "Michael Smith", "Emily Davis", "James Brown", "Olivia Wilson",
    "Daniel Martinez", "Sophia Anderson", "David Thomas", "Isabella Taylor", "Matthew Moore"
]

def generate_username(fullname):
    base = "".join(fullname.lower().split())
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=3))
    return base + suffix

def human_typing(element, text, min_delay=0.1, max_delay=0.3):
    for char in text:
        element.send_keys(char)
        sleep(random.uniform(min_delay, max_delay))

def human_sleep(min_t=1, max_t=3):
    sleep(random.uniform(min_t, max_t))

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1"
    )
    chrome_options.add_argument("--incognito")
    service = ChromeService()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    logger.success("✅ Chrome with mobile user agent started.")
    return driver

class InstagramBot:
    def __init__(self):
        mode = input("Auto-generate (a) or write your own (w)?: ").strip().lower()
        if mode in ["a", "auto"]:
            email, password, token = create_mailtm_account()
            if not all([email, password, token]):
                logger.error("Account creation failed! Exiting.")
                exit(1)
            self.email = email
            self.token = token
            self.password = password
            self.fullname = random.choice(NAMES)
            self.username = generate_username(self.fullname)
            self.day = str(random.randint(1, 28))
            self.month = str(random.randint(1, 12))
            self.year = str(random.randint(1960, 2005))
            logger.success(
                f"Generated:\nEmail: {self.email}\nUsername: {self.username}\nPassword: {self.password}"
            )
        else:
            self.email = input("Email: ")
            self.fullname = input("Full name: ")
            self.username = input("Username: ")
            self.password = input("Password: ")
            d, m, y = input("Birthday (D/M/Y): ").split("/")
            self.day, self.month, self.year = d, m, y
            self.token = None
        self.driver = get_driver()

    def create_account(self):
        d = self.driver
        d.get("https://www.instagram.com/accounts/signup/email/")
        human_sleep(2)
        # Handle cookie popup
        try:
            ck_button = WebDriverWait(d, 6).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(),'all cookies')]"))
            )
            ck_button.click()
            human_sleep(1)
        except:
            pass

        email_field = WebDriverWait(d, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Email']"))
        )
        human_typing(email_field, self.email)
        next_btn = WebDriverWait(d, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='Next']"))
        )
        next_btn.click()
        human_sleep(2)
        logger.success("✅ Email entered and Next clicked.")

        # Verification code
        if self.token:
            code = wait_for_mailtm_code(self.token)
            if code:
                code_field = WebDriverWait(d, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Confirmation code']"))
                )
                code_field.clear()
                human_typing(code_field, code)
                next_btn2 = WebDriverWait(d, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='Next']"))
                )
                human_sleep(1, 2)
                next_btn2.click()
                logger.success("✅ Confirmation code entered and Next clicked.")
            else:
                logger.error("❌ Did not receive verification code. Try again.")
                return

        # Continue registration
        WebDriverWait(d, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Password']"))
        ).send_keys(self.password)
        next_btn = WebDriverWait(d, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='Next']"))
        )
        next_btn.click()
        human_sleep(2)

        bday = f"{int(self.year)}-{int(self.month):02}-{int(self.day):02}"
        bd_field = WebDriverWait(d, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Birthday']"))
        )
        bd_field.clear()
        bd_field.send_keys(bday)
        next_btn = WebDriverWait(d, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='Next']"))
        )
        next_btn.click()
        human_sleep(2)

        WebDriverWait(d, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Full name']"))
        ).send_keys(self.fullname)
        next_btn = WebDriverWait(d, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='Next']"))
        )
        next_btn.click()
        human_sleep(2)

        WebDriverWait(d, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Username']"))
        ).send_keys(self.username)
        next_btn = WebDriverWait(d, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='Next']"))
        )
        next_btn.click()
        human_sleep(2)
        logger.success("✅ All registration steps finished successfully.")

    def close(self):
        try:
            self.driver.quit()
        except:
            pass

if __name__ == "__main__":
    logger.success("🚀 Starting Instagram account creation bot...")
    bot = InstagramBot()
    bot.create_account()
