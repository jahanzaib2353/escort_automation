"""Configuration for the report automation."""

POST_URL = "https://escortalligator.com.listcrawler.eu/post/escorts/canada/alberta/calgary/215157913"

# Optional: Add a residential proxy here if your IP is flagged (e.g., "http://user:pass@1.2.3.4:8080")
# Leaving it empty ("") will use your local network IP.
PROXY = ""

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

TWOCAPTCHA_API_KEY = "YOUR_2CAPTCHA_API_KEY_HERE"  # 
TWOCAPTCHA_API_URL = "http://2captcha.com/in.php"
TWOCAPTCHA_RES_URL = "http://2captcha.com/res.php"