"""Report-form actions."""

import time
import random
import string
import logging
import base64
import requests

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from config import (
    REPORT_BUTTON, REPORT_DETAILS, REPORT_TYPE_SCAM, REPORT_EMAIL, REPORT_SUBMIT,
    CAPTCHA_IMG, CAPTCHA_RELOAD, CAPTCHA_INPUT, CAPTCHA_IMAGE_WAIT,
    DEFAULT_WAIT, SHORT_WAIT, TWOCAPTCHA_API_KEY, TWOCAPTCHA_API_URL, TWOCAPTCHA_RES_URL,
)

log = logging.getLogger(__name__)

class ActionError(Exception):
    """Raised when a report action cannot complete."""

def _wait(driver, timeout=DEFAULT_WAIT):
    return WebDriverWait(driver, timeout)

def _safe_click(driver, el, label=""):
    try:
        el.click()
        log.info(f"  Clicked {label} (normal).")
    except Exception:
        driver.execute_script("arguments[0].click();", el)
        log.info(f"  Clicked {label} (JS fallback).")

def open_post(driver, url: str) -> None:
    log.info(f"Opening {url}")
    driver.get(url)
    _wait(driver, DEFAULT_WAIT).until(lambda d: d.execute_script("return document.readyState") == "complete")

def click_report_button(driver) -> None:
    log.info("Clicking REPORT button...")
    btn = _wait(driver, DEFAULT_WAIT).until(EC.element_to_be_clickable((By.CSS_SELECTOR, REPORT_BUTTON)))
    _safe_click(driver, btn, label="REPORT")
    _wait(driver, SHORT_WAIT).until(EC.visibility_of_element_located((By.CSS_SELECTOR, REPORT_DETAILS)))

def _random_details() -> str:
    words = ["spam", "fake", "duplicate", "suspicious", "misleading", "scam", "reported", "listing"]
    return " ".join(random.choice(words) for _ in range(random.randint(4, 8)))

def fill_details(driver, text: str | None = None) -> str:
    text = text or _random_details()
    log.info(f"Filling details: {text!r}")
    el = _wait(driver, SHORT_WAIT).until(EC.visibility_of_element_located((By.CSS_SELECTOR, REPORT_DETAILS)))
    el.clear()
    el.send_keys(text)
    return text

def select_scam_report(driver) -> None:
    log.info("Selecting Scam Report radio...")
    radio = _wait(driver, SHORT_WAIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, REPORT_TYPE_SCAM)))
    if not radio.is_selected():
        try:
            _safe_click(driver, radio.find_element(By.XPATH, "./ancestor::label[1]"), label="Scam Report label")
        except NoSuchElementException:
            _safe_click(driver, radio, label="Scam Report radio")
    driver.execute_script("arguments[0].click();", radio)
    log.info("  Scam Report selected ✓")

def fill_email(driver, email: str | None = None) -> str:
    email = email or f"{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}@example.com"
    log.info(f"Filling email: {email}")
    el = _wait(driver, SHORT_WAIT).until(EC.visibility_of_element_located((By.CSS_SELECTOR, REPORT_EMAIL)))
    el.clear()
    el.send_keys(email)
    return email

def _captcha_has_src(driver) -> bool:
    try:
        src = (driver.find_element(By.CSS_SELECTOR, CAPTCHA_IMG).get_attribute("src") or "").strip()
        return bool(src) and not src.endswith("#")
    except NoSuchElementException:
        return False

def reload_captcha(driver) -> None:
    btn = _wait(driver, SHORT_WAIT).until(EC.element_to_be_clickable((By.CSS_SELECTOR, CAPTCHA_RELOAD)))
    _safe_click(driver, btn, label="captcha reload")
    time.sleep(1.5)

def wait_for_captcha_image(driver, timeout: int = CAPTCHA_IMAGE_WAIT) -> None:
    try:
        _wait(driver, timeout).until(lambda d: _captcha_has_src(d))
    except TimeoutException:
        reload_captcha(driver)
        _wait(driver, timeout).until(lambda d: _captcha_has_src(d))

def download_captcha_bytes(driver) -> bytes:
    img = _wait(driver, SHORT_WAIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, CAPTCHA_IMG)))
    src = (img.get_attribute("src") or "").strip()
    if src.startswith("//"): src = "https:" + src

    session = requests.Session()
    for c in driver.get_cookies():
        session.cookies.set(c["name"], c["value"], domain=c.get("domain"), path=c.get("path", "/"))
    
    r = session.get(src, headers={"User-Agent": driver.execute_script("return navigator.userAgent;"), "Referer": driver.current_url}, timeout=30)
    r.raise_for_status()
    return r.content

def solve_captcha_2captcha(image_bytes: bytes) -> str:
    payload = {"key": TWOCAPTCHA_API_KEY, "method": "base64", "body": base64.b64encode(image_bytes).decode("utf-8"), "json": 1}
    resp = requests.post(TWOCAPTCHA_API_URL, data=payload, timeout=30).json()
    if resp.get("status") != 1: raise ActionError(f"2captcha submit failed: {resp.get('request')}")
    
    for _ in range(24):
        time.sleep(5)
        res = requests.get(f"{TWOCAPTCHA_RES_URL}?key={TWOCAPTCHA_API_KEY}&action=get&id={resp['request']}&json=1", timeout=15).json()
        if res.get("status") == 1: return res["request"]
        if res.get("request") != "CAPCHA_NOT_READY": raise ActionError(f"2captcha error: {res.get('request')}")
    raise ActionError("2captcha timed out")

def fill_captcha_input(driver, code: str) -> None:
    el = _wait(driver, SHORT_WAIT).until(EC.visibility_of_element_located((By.CSS_SELECTOR, CAPTCHA_INPUT)))
    el.clear()
    el.send_keys(code)

def submit_report(driver) -> None:
    log.info("Clicking SEND REPORT...")
    btn = _wait(driver, SHORT_WAIT).until(EC.element_to_be_clickable((By.CSS_SELECTOR, REPORT_SUBMIT)))
    _safe_click(driver, btn, label="SEND REPORT")

def solve_turnstile(driver) -> str | None:
    sitekey = driver.execute_script("""
        const el = document.querySelector('[data-sitekey]');
        if (el) return el.getAttribute('data-sitekey');
        for (let s of document.querySelectorAll('script')) {
            const m = s.textContent.match(/sitekey['"\\s:]+(['"]?)([0-9a-zA-Z_-]{40,})\\1/);
            if (m) return m[2];
        }
        return null;
    """)
    if not sitekey: return None
    
    resp = requests.post(TWOCAPTCHA_API_URL, data={"key": TWOCAPTCHA_API_KEY, "method": "turnstile", "sitekey": sitekey, "pageurl": driver.current_url, "json": 1}, timeout=30).json()
    if resp.get("status") != 1: return None
    
    for _ in range(24):
        time.sleep(5)
        res = requests.get(f"{TWOCAPTCHA_RES_URL}?key={TWOCAPTCHA_API_KEY}&action=get&id={resp['request']}&json=1", timeout=15).json()
        if res.get("status") == 1: return res["request"]
    return None

def handle_human_verification(driver) -> bool:
    """
    FINAL SOLUTION FOR MANAGED CHALLENGES:
    1. Simulates human mouse movements (Cloudflare actively checks for this).
    2. Waits for the clean undetected-chromedriver fingerprint to auto-resolve.
    3. Falls back to iframe clicking if a widget renders.
    """
    blocking_xpath = '//p[contains(text(), "This website uses a security service to protect against malicious bots")]'
    try:
        _wait(driver, 10).until(EC.presence_of_element_located((By.XPATH, blocking_xpath)))
        log.info("  Managed verification challenge detected!")
    except TimeoutException:
        return True

    # 1. Simulate human mouse movements (CRITICAL for Managed Challenges)
    log.info("  Simulating human mouse movements to bypass bot detection...")
    for _ in range(5):
        driver.execute_script("""
            const event = new MouseEvent('mousemove', {
                view: window, bubbles: true, cancelable: true,
                clientX: Math.random() * window.innerWidth,
                clientY: Math.random() * window.innerHeight
            });
            document.dispatchEvent(event);
        """)
        time.sleep(random.uniform(1.5, 3.0))

    # 2. Wait for auto-resolution (Clean undetected-chromedriver often passes automatically)
    log.info("  Waiting for Cloudflare to evaluate browser fingerprint (up to 25s)...")
    for _ in range(25):
        if not driver.find_elements(By.XPATH, blocking_xpath):
            log.info("  Challenge auto-resolved successfully! ✓")
            return True
        time.sleep(1)

    # 3. Fallback: If a Turnstile iframe rendered, switch to it and click
    try:
        iframe = _wait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//iframe[contains(@src, "challenges.cloudflare.com")]')))
        driver.switch_to.frame(iframe)
        try:
            checkbox = _wait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, '//input[@type="checkbox"] | //span[contains(text(), "Verify")]')))
            driver.execute_script("arguments[0].click();", checkbox)
            log.info("  Clicked Turnstile checkbox inside iframe.")
        except TimeoutException:
            pass
        finally:
            driver.switch_to.default_content()
        
        # Wait again after clicking
        for _ in range(15):
            if not driver.find_elements(By.XPATH, blocking_xpath):
                log.info("  Challenge resolved after iframe click! ✓")
                return True
            time.sleep(1)
    except TimeoutException:
        pass

    # 4. Last resort: Try 2Captcha Turnstile if a sitekey appeared
    token = solve_turnstile(driver)
    if token:
        driver.execute_script(f"""
            const input = document.querySelector('input[name="cf-turnstile-response"]');
            if (input) {{ input.value = '{token}'; input.dispatchEvent(new Event('change', {{ bubbles: true }})); }}
        """)
        time.sleep(5)
        if not driver.find_elements(By.XPATH, blocking_xpath):
            log.info("  Challenge resolved via 2Captcha token! ✓")
            return True

    log.error("  Automated verification failed. The managed challenge is blocking progress.")
    return False