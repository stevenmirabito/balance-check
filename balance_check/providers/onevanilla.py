import sys
import requests
from bs4 import BeautifulSoup
from balance_check import logger, captcha_solver, config
from balance_check.providers import BalanceCheckProvider
from balance_check.validators.credit_card import Issuer, CreditCardSchema


class OneVanilla(BalanceCheckProvider):
    def __init__(self):
        super().__init__()

        self.website_url = "https://www.onevanilla.com"
        self.schema = CreditCardSchema([Issuer.Visa])

    def scrape(self, fields):
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
            }
        )

        logger.info("Fetching balance check page")
        resp = session.get(self.website_url)
        if resp.status_code != 200:
            logger.critical(
                f"Failed to GET OneVanilla website (status code {resp.status_code})"
            )
            sys.exit(1)

        print(resp.text)

        page_html = BeautifulSoup(resp.content, features="html.parser")

        action = page_html.find("form")["action"]  # brandLoginForm
        fields["csrfToken"] = page_html.find("input", name="csrfToken")["value"]

        session.headers.update(
            {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": self.website_url,
                "origin": "https://www.simon.com",
            }
        )

        logger.info("Fetching card balance")
        form_resp = session.post(self.website_url + action[2:], data=fields)
        if form_resp.status_code != 200:
            logger.critical(
                f"Failed to retrieve card balance (status code {form_resp.status_code})"
            )
            sys.exit(1)

        balance_html = BeautifulSoup(form_resp.content, features="html.parser")

        try:
            avail_balance = balance_html.find("li", id="Avlbal").text.strip()
            # initial_balance = balance_html.find("li", text="Original Value:") #[-1].text.strip()
            initial_balance = "1"
        except:
            print("DUMP:", resp.text)
            raise RuntimeError("Could not find balance on page")

        logger.info(f"Success! Card balance: {avail_balance}")

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
                    "cardNumber": kwargs["card_number"],
                    "expMonth": kwargs["exp_month"],
                    "expYear": kwargs["exp_year"],
                    "cvv": kwargs["cvv"],
                }
            )
