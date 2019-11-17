import re
import requests
from bs4 import BeautifulSoup
from balance_check import logger, config
from balance_check.utils.captcha import CaptchaSolver
from balance_check.provider import BalanceCheckProvider
from balance_check.validators.credit_card import Issuer, CreditCardSchema


class Spafinder(BalanceCheckProvider):
    def __init__(self):
        super().__init__()

        self.base_url = "https://www.spafinder.com"
        self.website_url = "{}/pages/card-balance-inquiry/vpln/".format(self.base_url)
        self.schema = CreditCardSchema([Issuer.Visa])

    def scrape(self, fields):
        session = requests.Session()
        session.headers.update({"User-Agent": config.USER_AGENT})

        logger.info("Fetching balance check page")

        resp = session.get(self.website_url)
        if resp.status_code != 200:
            raise RuntimeError(
                "Failed to GET Spafinder website (status code {})".format(
                    resp.status_code
                )
            )

        page_html = BeautifulSoup(resp.content, features="html.parser")
        inquiry = page_html.find(id="balance-inquiry")
        form = inquiry.find("form")
        if not form:
            raise RuntimeError("Unable to find balance check form")

        endpoint = "{}{}".format(self.base_url, form["action"])

        # Page has bad HTML, need to search from top level
        recaptcha_field = page_html.find("div", class_="g-recaptcha")
        if not recaptcha_field:
            raise RuntimeError("Unable to find reCAPTCHA")

        site_key = recaptcha_field["data-sitekey"]

        logger.info("Solving reCAPTCHA (~30s)")

        captcha_solver = CaptchaSolver(api_key=config.ANTI_CAPTCHA_KEY)
        captcha_resp = captcha_solver.solve_recaptcha(self.website_url, site_key)
        if captcha_resp["errorId"] != 0:
            raise RuntimeError(
                "Unable to solve reCAPTCHA ({})".format(
                    captcha_resp["errorDescription"]
                )
            )

        fields["g-recaptcha-response"] = captcha_resp["solution"]["gRecaptchaResponse"]

        logger.info("Fetching card balance")

        form_resp = session.post(endpoint, data=fields)
        if form_resp.status_code != 200:
            raise RuntimeError(
                "Failed to retrieve card balance (status code {})".format(
                    form_resp.status_code
                )
            )

        resp_html = BeautifulSoup(form_resp.content, features="html.parser")
        error_html = resp_html.find("div", class_="alert-danger")
        if error_html:
            raise RuntimeError(
                "Got error while checking balance: {}".format(error_html.text)
            )

        balance_container = resp_html.find("div", class_="alert-success")
        if not balance_container:
            raise RuntimeError("Unable to find balance container")

        balance_match = re.search("(\d{1,2}\.\d{2})", balance_container.get_text())
        if not balance_match:
            raise RuntimeError("Unable to find balance text")

        balance = "${}".format(balance_match.group(0))

        logger.info("Success! Card balance: {}".format(balance))

        return {"balance": balance}

    def check_balance(self, **kwargs):
        if self.validate(kwargs):
            logger.info(
                "Checking balance for card: {}, exp {}/{}".format(
                    kwargs["card_number"], kwargs["exp_month"], kwargs["exp_year"]
                )
            )

            return self.scrape(
                {
                    "number-1": kwargs["card_number"],
                    "valid-mm": str(
                        int(kwargs["exp_month"])
                    ),  # Lazy way to strip '0' prefix, if present
                    "valid-yy": "20{}".format(kwargs["exp_year"]),
                    "pin": kwargs["cvv"],
                }
            )
