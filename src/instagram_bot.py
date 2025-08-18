import random
import string
import shutil
import os
import time
from time import sleep

from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from temp_mail import create_mailtm_account, wait_for_mailtm_code

NAMES = [
    "Alice Johnson",
    "Michael Smith",
    "Emily Davis",
    "James Brown",
    "Olivia Wilson",
    "Daniel Martinez",
    "Sophia Anderson",
    "David Thomas",
    "Isabella Taylor",
    "Matthew Moore",
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
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--incognito")

    service = ChromeService()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    logger.success("✅ Chrome WebDriver with Mobile User-Agent started successfully.")
    return driver

class InstagramBot:
    def __init__(self):
        mode = input("Do you want to be auto-generated or to write them yourself? (a/w):  ").lower()
        if mode in ["w", "write"]:
            self.phone_number = input("Phone_number or email:  ")
            self.fullname = input("Fullname:  ")
            self.username = input("Username:  ")
            self.password = input("Password:  ")
            d, m, y = input("Birth day: (D/M/Y) ").split("/")
            self.day, self.month, self.year = d, m, y
            self.token = None

        elif mode in ["a", "auto", "auto-generated"]:
            mail_data = create_mailtm_account()
            if not mail_data:
                logger.error("⚠️ Failed to create temporary email account.")
                exit(1)
            self.phone_number = mail_data[0]
            self.token = mail_data[2]
            self.fullname = random.choice(NAMES)
            self.username = generate_username(self.fullname)
            self.password = "".join(random.choices(string.ascii_letters + string.digits, k=12))
            self.day = str(random.randint(1, 28))
            self.month = str(random.randint(1, 12))
            self.year = str(random.randint(1960, 2005))
            logger.success(f"Generated credentials:\nEmail: {self.phone_number}\nUsername: {self.username}\nPassword: {self.password}")
        else:
            logger.error("Invalid mode. Choose 'a' or 'w'.")
            exit(1)

        want_pic = input("Do you want to add a profile picture? (y/n) ").lower()
        if want_pic in ["y", "yes"]:
            try:
                shutil.rmtree("C:\\Users\\lmoli\\Pictures\\Instagram profile image", ignore_errors=True)
                os.makedirs("C:\\Users\\lmoli\\Pictures\\Instagram profile image", exist_ok=True)
                location = input("Enter the path of your profile image:  ")
                if location.lower() not in ["n", "no", ""]:
                    shutil.move(location, "C:\\Users\\lmoli\\Pictures\\Instagram profile image\\descarga.jpg")
            except Exception as e:
                logger.error(f"⚠️ Failed to handle profile picture: {e}")

        self.driver = get_driver()

    def safe_click(self, xpath):
        try:
            el = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
            human_sleep(0.5, 1.5)
            el.click()
        except Exception as e:
            logger.error(f"⚠️ Failed safe click on {xpath}: {e}")

    def handle_cookie_popup(self):
        xpaths = [
            "//*[text()='Allow all cookies']",
            "//button[contains(text(),'Allow all cookies')]",
            "//button[contains(text(),'Accept All')]",
        ]
        for xpath in xpaths:
            try:
                el = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
                human_sleep(0.5, 1.5)
                el.click()
                logger.success("✅ Cookie popup accepted.")
                return
            except:
                continue
        logger.warning("⚠️ Cookie popup not found or already handled.")

    def wait_for_captcha_and_manual_solve(self):
        try:
            wait = WebDriverWait(self.driver, 8)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "g-recaptcha")))
            print("⚠️ Captcha detected! Please solve it manually, then press Enter to continue...")
            input()
        except:
            pass

    def create_account(self):
        d = self.driver
        d.get("https://www.instagram.com/accounts/signup/email/")
        human_sleep(2)

        self.handle_cookie_popup()
        human_sleep(1)

        # 🔹 وارد کردن ایمیل
        email_field = WebDriverWait(d, 15).until(
            EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Email']"))
        )
        human_typing(email_field, self.phone_number)

        # 🔹 کلیک روی Next واقعی بعد از ایمیل
        next_btn = WebDriverWait(d, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='Next']"))
        )
        next_btn.click()
        human_sleep(2)
        logger.success("✅ Email entered and Next clicked.")

        # 🔹 وارد کردن آخرین کد تایید ایمیل سریع و معتبر
        if self.token:
            code = None
            start_time = time.time()
            timeout = 180
            while time.time() - start_time < timeout:
                latest_code = wait_for_mailtm_code(self.token, timeout=5)  # آخرین پیام سریع
                if latest_code:
                    code = latest_code
                    break
                human_sleep(1, 2)
            
            if code:
                code_fields = d.find_elements(By.XPATH, "//input[@aria-label='Confirmation code']")
                code_field = next((f for f in code_fields if f.is_enabled() and f.is_displayed()), None)
                if code_field:
                    human_sleep(1.5, 2.5)
                    code_field.clear()
                    human_typing(code_field, code)
                    next_btn2 = WebDriverWait(d, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='Next']"))
                    )
                    human_sleep(1, 2)
                    next_btn2.click()
                    logger.success(f"✅ Confirmation code {code} entered and Next clicked.")
                else:
                    logger.error("⚠️ Confirmation code input not found!")
            else:
                logger.error("❌ No valid verification code received in time!")

        # 🔹 Password
        password_field = WebDriverWait(d, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Password']"))
        )
        human_typing(password_field, self.password)
        next_btn = WebDriverWait(d, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='Next']"))
        )
        next_btn.click()
        human_sleep(1.5, 2.5)

        # 🔹 Birthday
        birthday_field = WebDriverWait(d, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Birthday']"))
        )
        birthday_field.clear()
        birthday_field.send_keys(f"{int(self.year)}-{int(self.month):02}-{int(self.day):02}")
        next_btn = WebDriverWait(d, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='Next']"))
        )
        next_btn.click()
        human_sleep(1.5, 2.5)

        # 🔹 Full Name
        fullname_field = WebDriverWait(d, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Full name']"))
        )
        human_typing(fullname_field, self.fullname)
        next_btn = WebDriverWait(d, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='Next']"))
        )
        next_btn.click()
        human_sleep(1.5, 2.5)

        # 🔹 Username
        username_field = WebDriverWait(d, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@aria-label='Username']"))
        )
        username_field.clear()
        human_typing(username_field, self.username)
        next_btn = WebDriverWait(d, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='Next']"))
        )
        next_btn.click()
        human_sleep(1.5, 2.5)

        # 🔹 I agree
        agree_btn = WebDriverWait(d, 15).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and @aria-label='I agree']"))
        )
        agree_btn.click()
        human_sleep(2, 3)
        logger.success("✅ Account setup completed!")

    def close(self):
        try:
            self.driver.quit()
        except:
            pass

if __name__ == "__main__":
    logger.success("🚀 Starting Instagram account creation...")
    bot = InstagramBot()
    bot.create_account()
