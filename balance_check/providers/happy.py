import sys
import requests
from bs4 import BeautifulSoup
from balance_check import logger, captcha_solver, config
from balance_check.providers import BalanceCheckProvider
from balance_check.validators.credit_card import Issuer, CreditCardSchema


class Happy(BalanceCheckProvider):
    def __init__(self):
        super().__init__()

        self.website_url = "https://cardholder.happycards.com/check-your-balance"
        self.schema = CreditCardSchema([Issuer.Visa])

    def scrape(self, fields):
        session = requests.Session()
        session.headers.update({"User-Agent": config.USER_AGENT})

        logger.info("Fetching balance check page")

        resp = session.get(self.website_url)
        if resp.status_code != 200:
            logger.critical(
                f"Failed to GET Blackhawk website (status code {resp.status_code})"
            )
            sys.exit(1)

        page_html = BeautifulSoup(resp.content, features="html.parser")
        form = page_html.find("form")
        if not form:
            logger.critical("Unable to find balance check form")
            sys.exit(1)

        endpoint = "{}{}".format(self.website_url, form["action"])

        token_field = page_html.find(
            "input", attrs={"name": "__RequestVerificationToken"}
        )
        if not token_field:
            logger.critical("Failed to retrieve verification token")
            sys.exit(1)

        fields["__RequestVerificationToken"] = token_field["value"]

        recaptcha_field = page_html.find("div", class_="g-recaptcha")
        if not recaptcha_field:
            logger.critical("Unable to find reCAPTCHA")
            sys.exit(1)

        site_key = recaptcha_field["data-sitekey"]

        logger.info("Solving reCAPTCHA (~30s)")

        captcha = captcha_solver.solve_recaptcha(self.website_url, site_key)
        if captcha["errorId"] != 0:
            logger.critical(
                f"Unable to solve reCAPTCHA ({captcha['errorDescription']})"
            )
            sys.exit(1)

        fields["g-recaptcha-response"] = captcha["solution"]["gRecaptchaResponse"]

        logger.info("Fetching card balance")

        session.headers.update(
            {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.5",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Pragma": "no-cache",
                "Referer": self.website_url,
                "X-Requested-With": "XMLHttpRequest",
                "Host": "cardholder.happycards.com",
                "Origin": "https://cardholder.happycards.com",
            }
        )

        form_resp = session.post(endpoint, data=fields)
        if form_resp.status_code != 200:
            logger.critical(
                f"Failed to retrieve card balance (status code {form_resp.status_code})"
            )
            sys.exit(1)

        balance_html = BeautifulSoup(form_resp.content, features="html.parser")

        try:
            avail_balance = (
                balance_html.find("div", text="Available Balance")
                .parent.find("div", class_="value")
                .text
            )
        except:
            print("Couldnt read available balance from page.")
            print(form_resp.content)

        initial_balance = (
            balance_html.find("div", text="Initial Balance")
            .parent.find("div", class_="value")
            .text
        )

        logger.info("Success! Card balance: {}".format(avail_balance))

        return {"initial_balance": initial_balance, "available_balance": avail_balance}

    def check_balance(self, **kwargs):
        if self.validate(kwargs):
            logger.info(
                "Checking balance for card: {}, exp {}/{}".format(
                    kwargs["card_number"], kwargs["exp_month"], kwargs["exp_year"]
                )
            )

            return self.scrape(
                {
                    "CardNumber": kwargs["card_number"],
                    "ExpirationDateMonth": kwargs["exp_month"],
                    "ExpirationDateYear": kwargs["exp_year"],
                    "SecurityCode": kwargs["cvv"],
                }
            )
