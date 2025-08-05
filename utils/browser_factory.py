import undetected_chromedriver as uc

# if proxy:
#     options.add_argument(f"--proxy-server={proxy}")

def create_browser(proxy=None, headless=False):
    options = uc.ChromeOptions()
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
    if headless:
        options.add_argument("--headless")
    options.add_argument("--mute-audio")
    options.add_argument("--disable-blink-features=AutomationControlled")
    return uc.Chrome(options=options)