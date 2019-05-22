import requests
from bs4 import BeautifulSoup
from balance_check import logger, captcha_solver, config
from balance_check.providers import BalanceCheckProvider
from balance_check.validators.gift_card import Merchant, GiftCardSchema


class GameStop(BalanceCheckProvider):
    def __init__(self):
        super().__init__()

        self.website_url = "https://www.gamestop.com/profiles/valuelookup.aspx"
        self.schema = GiftCardSchema(Merchant.GameStop)
        self.max_workers = 1  # For some reason does not work properly multithreaded

    def scrape(self, fields):
        session = requests.Session()
        session.headers.update({"User-Agent": config.USER_AGENT})

        logger.info("Fetching balance check page")

        resp = session.get(self.website_url)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Failed to GET website (status code {resp.status_code})"
            )

        page_html = BeautifulSoup(resp.content, features="html.parser")
        form = page_html.find("form")
        if not form:
            raise RuntimeError("Unable to find balance check form")

        endpoint = f"{self.website_url}{form['action']}"

        # These fields are present on GS balance check page, does not work without including them
        fields["__EVENTTARGET"] = ""
        fields["__EVENTARGUMENT"] = ""
        fields["__LASTFOCUS"] = ""
        fields["__VIEWSTATE"] = page_html.find("input", id="__VIEWSTATE")["value"]
        fields["__VIEWSTATEGENERATOR"] = page_html.find(
            "input", id="__VIEWSTATEGENERATOR"
        )["value"]

        recaptcha_field = page_html.find("div", class_="g-recaptcha")
        if not recaptcha_field:
            raise RuntimeError("Unable to find reCAPTCHA")

        site_key = recaptcha_field["data-sitekey"]

        logger.info("Solving reCAPTCHA (~30s)")

        captcha_resp = captcha_solver.solve_recaptcha(self.website_url, site_key)
        if captcha_resp["errorId"] != 0:
            raise RuntimeError(
                f"Unable to solve reCAPTCHA ({captcha_resp['errorDescription']})"
            )

        fields["g-recaptcha-response"] = captcha_resp["solution"]["gRecaptchaResponse"]

        logger.info("Fetching card balance")

        form_resp = session.post(endpoint, data=fields)
        if form_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to retrieve card balance (status code {form_resp.status_code})"
            )

        balance_html = BeautifulSoup(form_resp.content, features="html.parser")

        try:
            avail_balance = balance_html.find("span", class_="balancePrice").text
        except:
            # GS prunes old depleted cards from its system and throws an 'invalid' error
            # Set these as -1 to notate they gave invalid error but are likely actually zero balance
            if balance_html.find(text="The Gift Card number entered is invalid."):
                avail_balance = "-1"
            elif balance_html.find(text="The PIN number entered is invalid."):
                raise RuntimeError("Invalid PIN")
            elif balance_html.find(text="The code you entered is invalid."):
                raise RuntimeError("Invalid CAPTCHA answer supplied")
            else:
                raise RuntimeError(
                    "Could not find balance on retrieved page for unknown reason"
                )

        logger.info(f"Success! Card balance: {avail_balance}")

        return {"balance": avail_balance}

    def check_balance(self, **kwargs):
        if self.validate(kwargs):
            logger.info(f"Checking balance for card: {kwargs['card_number']}")

            form_inputs = {
                "ctl00$ctl00$BaseContentPlaceHolder$mainContentPlaceHolder$CardNumberTextBox": kwargs[
                    "card_number"
                ],
                "ctl00$ctl00$BaseContentPlaceHolder$mainContentPlaceHolder$PinTextBox": kwargs[
                    "pin"
                ],
            }

            return self.scrape(form_inputs)
        # else:
        # Invalid