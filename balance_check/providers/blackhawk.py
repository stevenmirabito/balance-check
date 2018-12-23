import sys
import requests
from bs4 import BeautifulSoup
from balance_check import logger, captcha_solver
from balance_check.providers import BalanceCheckProvider
from balance_check.validators.credit_card import Issuer, CreditCardSchema


class Blackhawk(BalanceCheckProvider):
    def __init__(self):
        super().__init__()

        self.website_url = "https://mygift.giftcardmall.com"
        self.schema = CreditCardSchema([Issuer.Visa])

    def scrape(self, fields):
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:64.0) Gecko/20100101 Firefox/64.0"
        })

        fields["X-Requested-With"] = "XMLHttpRequest"

        logger.info("Fetching balance check page")

        resp = session.get(self.website_url)
        if resp.status_code != 200:
            logger.critical("Failed to GET Blackhawk website (status code {})".format(resp.status_code))
            sys.exit(1)

        page_html = BeautifulSoup(resp.content, features="html.parser")
        transactions = page_html.find(id="CheckBalanceTransactions")
        form = transactions.find("form")
        if not form:
            logger.critical("Unable to find balance check form")
            sys.exit(1)

        endpoint = "{}{}".format(self.website_url, form["action"])

        token_field = transactions.find("input", attrs={"name": "__RequestVerificationToken"})
        if not token_field:
            logger.critical("Failed to retrieve verification token")
            sys.exit(1)

        fields["__RequestVerificationToken"] = token_field["value"]

        recaptcha_field = transactions.find("div", class_="g-recaptcha")
        if not recaptcha_field:
            logger.critical("Unable to find reCAPTCHA")
            sys.exit(1)

        site_key = recaptcha_field["data-sitekey"]

        logger.info("Solving reCAPTCHA (~30s)")

        captcha_resp = captcha_solver.solve_recaptcha(self.website_url, site_key)
        if captcha_resp["errorId"] != 0:
            logger.critical("Unable to solve reCAPTCHA ({})".format(captcha_resp["errorDescription"]))
            sys.exit(1)

        fields["g-recaptcha-response"] = captcha_resp["solution"]["gRecaptchaResponse"]

        logger.info("Fetching card balance")

        session.headers.update({
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.5",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Pragma": "no-cache",
            "Referer": "https://mygift.giftcardmall.com/",
            "X-Requested-With": "XMLHttpRequest"
        })

        form_resp = session.post(endpoint, data=fields)
        if form_resp.status_code != 200:
            logger.critical("Failed to retrieve card balance (status code {})".format(form_resp.status_code))
            sys.exit(1)

        balance_html = BeautifulSoup(form_resp.content, features="html.parser")

        avail_balance = balance_html \
            .find("div", text="Available Balance") \
            .parent \
            .find("div", class_="value") \
            .text

        initial_balance = balance_html \
            .find("div", text="Initial Balance") \
            .parent \
            .find("div", class_="value") \
            .text

        logger.info("Success! Card balance: {}".format(avail_balance))

        return ({
            "available": avail_balance,
            "initial": initial_balance
        })

    def check_balance(self, **kwargs):
        if self.validate(kwargs):
            logger.info("Checking balance for card: {}, exp {}/{}".format(
                kwargs["card_number"],
                kwargs["exp_month"],
                kwargs["exp_year"]
            ))

            return self.scrape({
                "CardNumber": kwargs["card_number"],
                "ExpirationDateMonth": kwargs["exp_month"],
                "ExpirationDateYear": kwargs["exp_year"],
                "SecurityCode": kwargs["cvv"]
            })
