from python3_anticaptcha.ImageToTextTask import ImageToTextTask
from python3_anticaptcha.NoCaptchaTaskProxyless import NoCaptchaTaskProxyless


class CaptchaSolver:
    def __init__(self, api_key):
        self.image_task = ImageToTextTask(anticaptcha_key=api_key)
        self.recaptcha_task = NoCaptchaTaskProxyless(anticaptcha_key=api_key)

    def solve_image_url(self, image_link):
        return self.image_task.captcha_handler(captcha_link=image_link)

    def solve_image_b64(self, image_b64):
        return self.image_task.captcha_handler(captcha_base64=image_b64)

    def solve_recaptcha(self, page_url, site_key):
        return self.recaptcha_task.captcha_handler(
            websiteURL=page_url, websiteKey=site_key
        )
