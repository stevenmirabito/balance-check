import requests
import time
from balance_check import logger, config
from balance_check.providers import BalanceCheckProvider
from balance_check.validators.gift_card import Merchant, GiftCardSchema


class BestBuy(BalanceCheckProvider):
    def __init__(self):
        super().__init__()

        self.website_url = "https://www.bestbuy.com/gift-card-balance/api/lookup"
        self.schema = GiftCardSchema(Merchant.BestBuy)
        self.num_runs = 0
        self.max_workers = 1  # Cannot run multithreaded, IP limited

    def scrape(self, **kwargs):
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": config.USER_AGENT,
                "accept": "application/json",
                "origin": "https://www.bestbuy.com",
                "content-type": "application/json",
                "referer": "https://www.bestbuy.com/digitallibrary/giftcard",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "en-US,en;q=0.9",
                "cache-control": "no-cache",
            }
        )
        payload = f'{{"cardNumber":"{kwargs["card_number"]}","pin":"{kwargs["pin"]}"}}'
        logger.info(f"Fetching balance from API")

        try:
            resp = session.post(self.website_url, data=payload, timeout=5)
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error on API post: {e}")
        if resp.status_code != 200:
            raise RuntimeError(
                f"Failed to get valid response from API (status code {resp.status_code})"
            )

        # TODO: Sometimes does not output balance or throw error, not sure why. Happens with IP temp block
        try:
            avail_balance = resp.json()["balance"]
        except:
            raise RuntimeError("Could not parse balance from JSON response")

        logger.info(f"Success! Card balance: {avail_balance}")
        # TODO: figure out cleaner way to do this, feature in main?
        self.num_runs += 1
        # Not sure exactly what sweet spot is but IP blocks at 10 min, 15 min seems good
        seconds = 3 if self.num_runs % 9 else 60 * 15 + 5
        logger.info(
            f"Ran {self.num_runs} times. Sleeping {seconds} seconds before trying next..."
        )
        time.sleep(seconds)

        return {"balance": avail_balance}

    def check_balance(self, **kwargs):
        if self.validate(kwargs):
            logger.info(f"Checking balance for card: {kwargs['card_number']}")

            return self.scrape(card_number=kwargs["card_number"], pin=kwargs["pin"])
        # else:
        # Invalid
