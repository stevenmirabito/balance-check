import re
from python3_anticaptcha.ImageToTextTask import ImageToTextTask
from python3_anticaptcha.NoCaptchaTaskProxyless import NoCaptchaTaskProxyless
from python3_anticaptcha.FunCaptchaTaskProxyless import FunCaptchaTaskProxyless

ARKOSE_KEY_REGEX = r"arkoselabs\.com\/v2\/([A-Z0-9]{8}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{12})"


def extract_arkose_key(html):
    match = re.search(ARKOSE_KEY_REGEX, html)
    return match.group(1) if match else None


class CaptchaSolver:
    def __init__(self, api_key):
        self.image_task = ImageToTextTask(anticaptcha_key=api_key)
        self.recaptcha_task = NoCaptchaTaskProxyless(anticaptcha_key=api_key)
        self.funcaptcha_task = FunCaptchaTaskProxyless(anticaptcha_key=api_key)

    def solve_image_url(self, image_link):
        return self.image_task.captcha_handler(captcha_link=image_link)

    def solve_image_b64(self, image_b64):
        return self.image_task.captcha_handler(captcha_base64=image_b64)

    def solve_recaptcha(self, page_url, site_key):
        return self.recaptcha_task.captcha_handler(
            websiteURL=page_url, websiteKey=site_key
        )

    def solve_funcaptcha(self, page_url, public_key):
        return self.funcaptcha_task.captcha_handler(
            websiteURL=page_url, websitePublicKey=public_key
        )
