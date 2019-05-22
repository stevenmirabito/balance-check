import requests
from bs4 import BeautifulSoup
import lxml.html
from balance_check import logger, captcha_solver, config
from balance_check.providers import BalanceCheckProvider
from balance_check.validators.gift_card import Merchant, GiftCardSchema


class GuitarCenter(BalanceCheckProvider):
    def __init__(self):
        super().__init__()

        self.website_url = "https://www.guitarcenter.com/Gift-Card/Balance.gc"
        self.schema = GiftCardSchema(Merchant.GuitarCenter)

    def scrape(self, **card):
        session = requests.Session()
        session.headers.update(
            {
                "user-agent": config.USER_AGENT,
                "accept": "*/*",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "en-US,en;q=0.9",
            }
        )
        params = {"giftCardNumber": card["number"], "pin": card["pin"]}

        logger.info(f"Fetching balance")
        resp = session.get(self.website_url, params=params)

        if resp.status_code != 200:
            raise RuntimeError(
                f"Failed to retrieve card balance (status code {form_resp.status_code})"
            )

        # Tried to use BS4 but it refused to work, I think HTML returned was too messy/non-compliant
        page_parsed = lxml.html.fromstring(resp.text)

        try:
            avail_balance = page_parsed.xpath("//div[@class='cardPoints']/div")[0].text
        except:
            # error on screen
            error_text = page_parsed.xpath("//div[contains(@class,'error')]")[0].text
            raise RuntimeError(error_text)

        logger.info(f"Success! Card balance: {avail_balance}")
        return {"balance": avail_balance}

    def check_balance(self, **kwargs):
        if self.validate(kwargs):
            logger.info(f"Checking balance for card: {kwargs['card_number']}")

            return self.scrape(number=kwargs["card_number"], pin=kwargs["pin"])
        # else:
        # Invalid
