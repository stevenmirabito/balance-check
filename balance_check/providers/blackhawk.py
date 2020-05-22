import requests
from bs4 import BeautifulSoup
from balance_check import logger, config
from balance_check.utils.captcha import CaptchaSolver, extract_arkose_key
from balance_check.provider import BalanceCheckProvider
from balance_check.validators.credit_card import Issuer, CreditCardSchema


class Blackhawk(BalanceCheckProvider):
    def __init__(self):
        super().__init__()

        self.website_url = "https://mygift.giftcardmall.com"
        self.schema = CreditCardSchema([Issuer.Visa])

    def scrape(self, fields):
        session = requests.Session()
        session.headers.update({"User-Agent": config.USER_AGENT})

        fields["X-Requested-With"] = "XMLHttpRequest"

        logger.info("Fetching balance check page")

        resp = session.get(self.website_url)
        if resp.status_code != 200:
            raise RuntimeError(
                f"Failed to GET Blackhawk website (status code {resp.status_code})"
            )

        page_html = BeautifulSoup(resp.content, features="html.parser")
        transactions = page_html.find(id="CheckBalanceTransactions")
        form = transactions.find("form")
        if not form:
            raise RuntimeError("Unable to find balance check form")

        endpoint = "{}{}".format(self.website_url, form["action"])

        token_field = transactions.find(
            "input", attrs={"name": "__RequestVerificationToken"}
        )
        if not token_field:
            raise RuntimeError("Failed to retrieve verification token")

        fields["__RequestVerificationToken"] = token_field["value"]

        arkose_key = extract_arkose_key(resp.text)
        if not arkose_key:
            raise RuntimeError("Failed to extract Arkose Labs public key")

        logger.info("Solving FunCaptcha (~30s)")

        captcha_solver = CaptchaSolver(api_key=config.ANTI_CAPTCHA_KEY)
        captcha = captcha_solver.solve_funcaptcha(self.website_url, arkose_key)
        if captcha["errorId"] != 0:
            raise RuntimeError(
                "Unable to solve FunCaptcha ({})".format(captcha["errorDescription"])
            )

        fields["captchaToken"] = captcha["solution"]["token"]

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
                "Referer": "https://mygift.giftcardmall.com/",
                "X-Requested-With": "XMLHttpRequest",
            }
        )

        form_resp = session.post(endpoint, data=fields)
        if form_resp.status_code != 200:
            raise RuntimeError(
                "Failed to retrieve card balance (status code {})".format(
                    form_resp.status_code
                )
            )

        balance_html = BeautifulSoup(form_resp.content, features="html.parser")

        avail_balance = (
            balance_html.find("div", text="Available Balance")
            .parent.find("div", class_="value")
            .text
        )

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
