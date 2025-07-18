from concurrent.futures import ThreadPoolExecutor
from watch_video import watch_video, get_cookie_files

if __name__ == "__main__":
    cookies = get_cookie_files()
    max_workers = 100  # تعداد اکانت همزمان

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(watch_video, cookies)
