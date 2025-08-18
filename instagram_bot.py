import json
import os
import random
import shutil
import string
from time import sleep

from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from temp_mail import create_mailtm_account, wait_for_mailtm_code  # فایل temp_mail.py که ساختی

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

def select_dropdown(driver, xpath, value):
    try:
        dropdown = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView(true);", dropdown)
        sleep(0.5)
        Select(dropdown).select_by_value(str(value))
        logger.success(f"✅ Selected value {value} for dropdown {xpath}")
    except Exception as e:
        logger.error(f"⚠️ Failed to select dropdown {xpath} with value {value}: {e}")

def save_account(username, password, email):
    data_path = "data/accounts.json"
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    accounts = []
    if os.path.exists(data_path):
        try:
            with open(data_path, encoding="utf-8") as f:
                accounts = json.load(f)
        except Exception as e:
            logger.error(f"⚠️ Failed to read accounts JSON file: {e}")
    accounts.append({
        "username": username,
        "password": password,
        "email": email,
    })
    try:
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(accounts, f, indent=4, ensure_ascii=False)
        logger.success(f"✅ Account saved to {data_path}")
    except Exception as e:
        logger.error(f"⚠️ Failed to save account to JSON file: {e}")

def human_typing(element, text, min_delay=0.1, max_delay=0.3):
    for char in text:
        element.send_keys(char)
        sleep(random.uniform(min_delay, max_delay))

def human_sleep(min_t=1, max_t=3):
    sleep(random.uniform(min_t, max_t))

def get_driver():
    try:
        chrome_options = Options()
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1",
        )
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--incognito")

        service = ChromeService()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.success("✅ Chrome WebDriver with Mobile User-Agent started successfully.")
        return driver
    except WebDriverException as e:
        logger.error(f"❌ Chrome WebDriver not available: {e}")
        exit(1)


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
            self.phone_number = mail_data[0]  # ایمیل
            self.token = mail_data[2]         # توکن
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
                import os
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
            sleep(0.5)
            el.click()
        except Exception as e:
            logger.error(f"⚠️ Failed safe click on {xpath}: {e}")

    def handle_cookie_popup(self):
        try:
            self.safe_click("//*[text()='Allow all cookies']")
        except:
            try:
                self.safe_click("//button[contains(text(),'Allow all cookies')]")
            except:
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
        d.get("https://www.instagram.com/accounts/emailsignup/")
        human_sleep(2)

        self.handle_cookie_popup()
        human_sleep(1)

        human_typing(d.find_element(By.NAME, "emailOrPhone"), self.phone_number)
        human_typing(d.find_element(By.NAME, "fullName"), self.fullname)
        human_typing(d.find_element(By.NAME, "username"), self.username)
        human_typing(d.find_element(By.NAME, "password"), self.password)

        self.safe_click("//button[@type='submit']")
        human_sleep(3)

        self.wait_for_captcha_and_manual_solve()

        select_dropdown(d, "(//select)[1]", self.month)
        select_dropdown(d, "(//select)[2]", self.day)
        select_dropdown(d, "(//select)[3]", self.year)

        self.safe_click("//button[contains(text(),'Next')]")
        human_sleep(5)

        if self.token:
            code = wait_for_mailtm_code(self.token)
            if code:
                try:
                    input_box = WebDriverWait(d, 20).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='email_confirmation_code']")))
                    input_box.send_keys(code)
                    self.safe_click("//button[contains(text(),'Confirm')]")
                    logger.success("✅ Verification code entered automatically.")
                except Exception as e:
                    logger.error(f"⚠️ Failed to enter verification code automatically: {e}")
                    manual_code = input("Enter the verification code manually: ")
                    input_box.send_keys(manual_code)
                    self.safe_click("//button[contains(text(),'Confirm')]")
            else:
                manual_code = input("Enter the verification code manually: ")
                input_box = d.find_element(By.XPATH, "//input[@name='email_confirmation_code']")
                input_box.send_keys(manual_code)
                self.safe_click("//button[contains(text(),'Confirm')]")
        else:
            manual_code = input("Enter the verification code manually: ")
            input_box = d.find_element(By.XPATH, "//input[@name='email_confirmation_code']")
            input_box.send_keys(manual_code)
            self.safe_click("//button[contains(text(),'Confirm')]")

        save_account(self.username, self.password, self.phone_number)

        # تغییر بیو
        try:
            d.get("https://www.instagram.com/accounts/edit/")
            human_sleep(3, 6)
            bio_box = WebDriverWait(d, 15).until(EC.element_to_be_clickable((By.NAME, "biography")))
            bio_box.clear()
            human_typing(bio_box, "Love traveling ✈️ | Coffee addict ☕️")
            human_sleep(1, 3)
            save_btn = d.find_element(By.XPATH, "//button[contains(text(),'Submit')]")
            save_btn.click()
            logger.success("✅ Bio updated successfully.")
        except Exception as e:
            logger.error(f"⚠️ Failed to update bio: {e}")

        # لایک یک پست در Explore
        try:
            d.get("https://www.instagram.com/explore/")
            human_sleep(5, 8)
            first_post = WebDriverWait(d, 15).until(EC.element_to_be_clickable((By.XPATH, "(//article//a)[1]")))
            first_post.click()
            human_sleep(3, 5)
            like_btn = WebDriverWait(d, 15).until(EC.element_to_be_clickable((By.XPATH, "//span[@aria-label='Like']")))
            like_btn.click()
            logger.success("✅ Liked a post successfully.")
        except Exception as e:
            logger.warning(f"⚠️ Could not like a post: {e}")

        human_sleep(7)

    def close(self):
        try:
            self.driver.quit()
        except:
            pass


if __name__ == "__main__":
    logger.success("🚀 Starting Instagram account creation...")
    bot = InstagramBot()
    bot.create_account()
