"""Selenium navigation and reporting main script."""

import logging
import time
from pathlib import Path

import undetected_chromedriver as uc
from selenium.common.exceptions import WebDriverException

from actions import (
    open_post, click_report_button, select_scam_report, fill_details, fill_email,
    wait_for_captcha_image, reload_captcha, download_captcha_bytes, solve_captcha_2captcha,
    fill_captcha_input, submit_report, handle_human_verification, ActionError,
)
from config import TARGET_URL, PROXY

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

DEBUG_DIR = Path("debug")

def build_driver():
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    if PROXY:
        options.add_argument(f"--proxy-server={PROXY}")
        log.info(f"✅ Using Proxy: {PROXY}")
    else:
        log.info("⚠️ No proxy set. Using local IP. (Edit PROXY in config.py to change this)")

    driver = uc.Chrome(options=options, headless=False)
    driver.set_page_load_timeout(30)
    
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """
    })
    return driver

def save_diagnostics(driver, url):
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    driver.save_screenshot(str(DEBUG_DIR / "selenium_debug.png"))
    (DEBUG_DIR / "selenium_debug.html").write_text(driver.page_source, encoding="utf-8")
    log.info("Diagnostics saved to %s", DEBUG_DIR.resolve())

def main():
    driver = None
    try:
        driver = build_driver()
        
        log.info("=== Step 1: Open Target Profile ===")
        open_post(driver, TARGET_URL)

        log.info("=== Step 2: Click Report Button ===")
        click_report_button(driver)

        log.info("=== Step 3: Fill Form Details ===")
        select_scam_report(driver)
        fill_details(driver)
        fill_email(driver)

        log.info("=== Step 4: Handle Form Captcha ===")
        for attempt in range(2):
            try:
                wait_for_captcha_image(driver)
                fill_captcha_input(driver, solve_captcha_2captcha(download_captcha_bytes(driver)))
                break
            except ActionError as e:
                log.warning(f"  Captcha attempt {attempt + 1} failed: {e}")
                if attempt == 0: reload_captcha(driver)
        else:
            manual = input("  ACTION REQUIRED: Enter captcha manually (or press Enter to skip): ").strip()
            if manual: fill_captcha_input(driver, manual)

        log.info("=== Step 5: Submit Report ===")
        submit_report(driver)
        
        log.info("=== Step 6: Handle Post-Submission Verification ===")
        if not handle_human_verification(driver):
            log.info("=" * 70)
            log.info("ACTION REQUIRED: Automated verification did not clear the page.")
            log.info("Please manually click the checkbox if it appears.")
            log.info("The script will wait here for 120 seconds...")
            log.info("=" * 70)
            time.sleep(120)

        log.info("✅ Report process completed successfully.")
        input("\nBrowser is open. Inspect the page, then press ENTER to close...")

    except KeyboardInterrupt:
        log.info("Interrupted by user.")
    except Exception as exc:
        log.exception("Automation failed: %s", exc)
        if driver: save_diagnostics(driver, TARGET_URL)
        input("Press ENTER to exit...")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    main()