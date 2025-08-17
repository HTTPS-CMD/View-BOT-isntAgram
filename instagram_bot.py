import random
import string
import time
import shutil
from datetime import datetime
from time import sleep
import json
import os

from loguru import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.safari.service import Service as SafariService
from selenium.common.exceptions import WebDriverException

from temp_mail import create_mailtm_account, wait_for_mailtm_code  # فایل temp_mail.py که ساختی


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
            with open(data_path, "r", encoding="utf-8") as f:
                accounts = json.load(f)
        except Exception as e:
            logger.error(f"⚠️ Failed to read accounts JSON file: {e}")
    accounts.append({
        "username": username,
        "password": password,
        "email": email
    })
    try:
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(accounts, f, indent=4, ensure_ascii=False)
        logger.success(f"✅ Account saved to {data_path}")
    except Exception as e:
        logger.error(f"⚠️ Failed to save account to JSON file: {e}")


def get_driver():
    try:
        safari_service = SafariService()
        driver = webdriver.Safari(service=safari_service)
        logger.success("✅ Safari WebDriver started successfully.")
        return driver
    except WebDriverException as e:
        logger.error(f"❌ Safari WebDriver not available: {e}")
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
            self.fullname = "Auto User"
            self.username = "user_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
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
        sleep(2)

        self.handle_cookie_popup()
        sleep(1)

        d.find_element(By.NAME, "emailOrPhone").send_keys(self.phone_number)
        d.find_element(By.NAME, "fullName").send_keys(self.fullname)
        d.find_element(By.NAME, "username").send_keys(self.username)
        d.find_element(By.NAME, "password").send_keys(self.password)

        self.safe_click("//button[@type='submit']")
        sleep(3)

        self.wait_for_captcha_and_manual_solve()

        select_dropdown(d, "(//select)[1]", self.month)
        select_dropdown(d, "(//select)[2]", self.day)
        select_dropdown(d, "(//select)[3]", self.year)

        self.safe_click("//button[contains(text(),'Next')]")
        sleep(5)

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

        sleep(7)

    def close(self):
        try:
            self.driver.quit()
        except:
            pass


if __name__ == "__main__":
    logger.success("🚀 Starting Instagram account creation...")
    bot = InstagramBot()
    bot.create_account()
