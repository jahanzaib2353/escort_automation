"""Configuration for the report automation."""

# ==========================================
# USER SETTINGS - CHANGE THESE VALUES
# ==========================================

# 1. The profile URL you want to report
TARGET_URL = "https://escortalligator.com.listcrawler.eu/post/escorts/canada/alberta/calgary/215157913"

# 2. Your real email address for the report confirmation
TARGET_EMAIL = "kat_kat231@example.com"  # <-- REPLACE THIS WITH YOUR ACTUAL EMAIL

# 3. Your Residential Proxy (Highly Recommended to avoid IP flags)
# Format: "http://username:password@ip_address:port"
# Example: "http://myuser:mypass@192.168.1.100:8080"
# Leave as "" (empty quotes) if you don't have one, but using a residential proxy is safest.
PROXY = "" 

# ==========================================
# DO NOT CHANGE ANYTHING BELOW THIS LINE
# ==========================================

REPORT_BUTTON = "div#reportButton"
REPORT_DETAILS = "textarea#reportPostDetails"
REPORT_TYPE_SCAM = "input[type='radio'][value='SCAM']"
REPORT_EMAIL = "input#postReportEmailConfirmation"
CAPTCHA_IMG = "img#captcha_image_itself"
CAPTCHA_RELOAD = "div.replyCaptchaReloadButton a"
CAPTCHA_INPUT = "input#captcha_code"
REPORT_SUBMIT = "input#postReportButtonSend"

DEFAULT_WAIT = 10
SHORT_WAIT = 5
CAPTCHA_IMAGE_WAIT = 10

TWOCAPTCHA_API_KEY = "YOUR_2CAPTCHA_API_KEY_HERE"  # Keep your API key here
TWOCAPTCHA_API_URL = "http://2captcha.com/in.php"
TWOCAPTCHA_RES_URL = "http://2captcha.com/res.php"