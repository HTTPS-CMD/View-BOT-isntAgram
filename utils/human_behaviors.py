import time
import random
from selenium.webdriver.common.action_chains import ActionChains

def human_scroll(driver):
    total_scrolls = random.randint(3, 6)
    for _ in range(total_scrolls):
        scroll_by = random.randint(200, 600)
        driver.execute_script(f"window.scrollBy(0, {scroll_by});")
        time.sleep(random.uniform(1.5, 3.5))

def human_mouse_move(driver):
    actions = ActionChains(driver)
    for _ in range(random.randint(10, 20)):
        x = random.randint(0, driver.execute_script("return window.innerWidth"))
        y = random.randint(0, driver.execute_script("return window.innerHeight"))
        try:
            actions.move_by_offset(x, y).perform()
        except:
            pass
        time.sleep(random.uniform(0.2, 0.6))
