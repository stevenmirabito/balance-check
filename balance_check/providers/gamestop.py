import json
from urllib import request
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from http.cookiejar import CookieJar
from balance_check import logger, config
from balance_check.utils import deep_get
from balance_check.utils.captcha import CaptchaSolver
from balance_check.providers import BalanceCheckProvider
from balance_check.validators.gift_card import Merchant, GiftCardSchema

HEADERS = {
    "user-agent": config.USER_AGENT,
}


class GameStop(BalanceCheckProvider):
    def __init__(self):
        super().__init__()

        self.website_url = "https://www.gamestop.com/giftcards/"
        self.api_endpoint = "https://www.gamestop.com/on/demandware.store/Sites-gamestop-us-Site/default/GiftCard-BalanceCheck"
        self.schema = GiftCardSchema(Merchant.GameStop)
        self.max_workers = 1  # For some reason does not work properly multithreaded

    def scrape(self, **kwargs):
        cookies = CookieJar()
        opener = request.build_opener(request.HTTPCookieProcessor(cookies))

        logger.info("Fetching balance check page")

        # Use urllib directly as requests gets blocked
        req = request.Request(self.website_url, headers=HEADERS)
        resp = opener.open(req)

        if resp.status != 200:
            raise RuntimeError(
                f"Failed to get GameStop website (status code {resp.status})"
            )

        page_html = BeautifulSoup(resp.read(), features="html.parser")

        recaptcha_el = page_html.find("div", {"data-sitekey": True})
        if not recaptcha_el:
            raise RuntimeError("Unable to find reCAPTCHA on page")

        csrf_el = page_html.find("input", {"name": "csrf_token"})
        if not csrf_el:
            raise RuntimeError("Unable to find CSRF on page")

        site_key = recaptcha_el["data-sitekey"]
        csrf_token = csrf_el["value"]

        logger.info("Solving reCAPTCHA (~30s)")

        captcha_solver = CaptchaSolver(api_key=config.ANTI_CAPTCHA_KEY)
        captcha_resp = captcha_solver.solve_recaptcha(self.website_url, site_key)
        if captcha_resp["errorId"] != 0:
            raise RuntimeError(
                f"Unable to solve reCAPTCHA ({captcha_resp['errorDescription']})"
            )

        payload = {
            "dwfrm_giftCard_balance_accountNumber": kwargs["card_number"],
            "dwfrm_giftCard_balance_pinNumber": kwargs["pin"],
            "g-recaptcha-response": captcha_resp["solution"]["gRecaptchaResponse"],
            "csrf_token": csrf_token,
        }

        logger.info("Fetching balance from API")

        try:
            req = request.Request(self.api_endpoint, headers=HEADERS)
            data = urlencode(payload).encode("utf-8")
            req.add_header(
                "Content-Type", "application/x-www-form-urlencoded; charset=UTF-8"
            )
            req.add_header("Content-Length", len(data))
            resp = opener.open(req, data)

            if resp.status != 200:
                raise RuntimeError(f"Invalid API response (status code {resp.status})")

            result = json.loads(
                resp.read().decode(resp.info().get_param("charset") or "utf-8")
            )
            errors = deep_get(result, "error")
            if errors:
                err = errors[0]
                raise RuntimeError(f"Failed to retrieve balance from API: {err}")

            balance = deep_get(result, "balance")
            if balance is None:
                raise RuntimeError(
                    f"Invalid API response: unable to find required key in JSON response"
                )

            logger.info(f"Success! Card balance: ${balance}")

            return {
                "balance": f"${balance}",
            }
        except json.JSONDecodeError:
            raise RuntimeError("Failed to parse API response as JSON")

    def check_balance(self, **kwargs):
        if self.validate(kwargs):
            logger.info(f"Checking balance for card: {kwargs['card_number']}")

            return self.scrape(card_number=kwargs["card_number"], pin=kwargs["pin"])
