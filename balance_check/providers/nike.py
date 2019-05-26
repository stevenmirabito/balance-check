import requests
from balance_check import logger
from balance_check.providers import BalanceCheckProvider
from balance_check.validators.gift_card import Merchant, GiftCardSchema


# TODO - not working, json response no good. needs cookie data?


class Nike(BalanceCheckProvider):
    def __init__(self):
        super().__init__()

        self.website_url = (
            "https://store.nike.com/us/en_us/?l=shop%2Cgift_cards&balance=true"
        )
        self.api_endpoint = (
            "https://store.nike.com/nikestore/html/services/giftCardBalanceCartService"
        )
        self.schema = GiftCardSchema(Merchant.Nike)
        self.max_workers = 1  # One thread is enough since you can do batches at a time
        self.max_simultaneous = 5

    def scrape(self, cards_chunk):
        session = requests.Session()
        session.headers.update(
            {
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "en-US,en;q=0.9",
            }
        )
        # Get balance page in session to retrieve cookies
        session.get(self.website_url)

        # Assemble a string for JSON request from cards chunk taken
        cards_str = ""
        for i, card in enumerate(cards_chunk):
            if i > 0:
                cards_str += ","
            cards_str += card["card_number"] + ":" + card["pin"]
        payload = {
            "gift_card_numbers": cards_str,
            "action": "checkCertificateBalance",
            "country": "US",
            "lang_locale": "en_US",
        }
        session.headers.update({"content-type": "application/x-www-form-urlencoded"})

        logger.info(f"Fetching balance from API")
        try:
            resp = session.post(self.api_endpoint, data=payload, timeout=5)
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error on API post: {e}")
        if resp.status_code != 200:
            raise RuntimeError(
                f"Failed to get valid response from API (status code {resp.status_code})"
            )

        print(resp.text)
        quit()
        # TODO: Sometimes does not output balance or throw error, not sure why. Happens with IP temp block
        # try:
        #     avail_balance = resp.json()["balance"]
        # except:
        #     raise RuntimeError("Could not parse balance from JSON response")

        # logger.info(f"Success! Card balance: {avail_balance}")
        # # TODO: figure out cleaner way to do this, feature in main?
        # self.num_runs += 1
        # # Not sure exactly what sweet spot is but IP blocks at 10 min, 15 min seems good
        # seconds = 3 if self.num_runs % 9 else 60*15+5
        # logger.info(f"Ran {self.num_runs} times. Sleeping {seconds} seconds before trying next...")
        # time.sleep(seconds)

        # return {"balance": avail_balance}

    def check_balance(self, cards_chunk):
        for card in cards_chunk:
            if not self.validate(card):
                raise RuntimeError(
                    f'Card format of {card["card_number"]} failed validation'
                )

        logger.info(f"Checking balance for cards in chunk")
        return self.scrape(cards_chunk)
        # else:
        # Invalid
