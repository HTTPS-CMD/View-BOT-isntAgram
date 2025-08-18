import os
import json
import time
import random
import undetected_chromedriver as uc
from utils.human_behaviors import human_mouse_move, human_scroll

VIDEO_URL = "https://www.instagram.com/reel/DGs2jGntCHJ/?utm_source=ig_web_copy_link"  # ← Set your Instagram video URL here
COOKIES_DIR = "data/cookies"
REPORT_FILE = "data/report.json"

report_data = {}

def get_cookie_files():
    return [f for f in os.listdir(COOKIES_DIR) if f.endswith(".json")]

def load_cookies(driver, cookie_file):
    with open(os.path.join(COOKIES_DIR, cookie_file), "r") as f:
        cookies = json.load(f)
    driver.get("https://www.instagram.com/")
    time.sleep(3)
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()
    time.sleep(3)

def is_account_blocked(driver):
    current_url = driver.current_url
    if "checkpoint" in current_url or "consent" in current_url:
        return True
    try:
        if "Instagram" not in driver.title:
            return True
    except:
        return True
    return False

def watch_video(username_file):
    username = username_file.replace(".json", "")
    print(f"🎥 [{username}] Watching video started...")

    options = uc.ChromeOptions()
    options.add_argument("--mute-audio")
    driver = uc.Chrome(options=options)

    views_done = 0

    try:
        load_cookies(driver, username_file)

        if is_account_blocked(driver):
            print(f"🚫 [{username}] Blocked or restricted.")
            report_data[username] = {
                "views": 0,
                "status": "blocked"
            }
            return

        for i in range(4):
            print(f"🔁 [{username}] View {i + 1}/4")
            driver.get(VIDEO_URL)
            time.sleep(random.uniform(4, 6))

            human_scroll(driver)
            human_mouse_move(driver)

            watch_time = random.randint(15, 25)
            print(f"⏱️ Watching for {watch_time} seconds...")
            time.sleep(watch_time)

            views_done += 1

            if i < 3:
                wait_time = 30  # 1 Seconds
                print(f"🕐 Waiting 1 Seconds before next view...")
                time.sleep(wait_time)

        print(f"✅ [{username}] All views completed.")

        report_data[username] = {
            "views": views_done,
            "status": "success" if views_done == 4 else "partial"
        }

    except Exception as e:
        print(f"❌ [{username}] Error: {e}")
        report_data[username] = {
            "views": views_done,
            "status": "error"
        }

    finally:
        driver.quit()

if __name__ == "__main__":
    all_cookies = get_cookie_files()
    for cookie_file in all_cookies:
        watch_video(cookie_file)
        delay = random.randint(60, 120)
        print(f"⏱️ Waiting {delay} seconds before next account...")
        time.sleep(delay)

    # Save report at the end
    with open(REPORT_FILE, "w") as f:
        json.dump(report_data, f, indent=2)
    print(f"📄 Report saved to {REPORT_FILE}")
