import requests
from json import JSONDecodeError
from balance_check import logger, config
from balance_check.utils import deep_get
from balance_check.utils.captcha import CaptchaSolver
from balance_check.provider import BalanceCheckProvider
from balance_check.validators.gift_card import Merchant, GiftCardSchema

HEADERS = {
    "user-agent": config.USER_AGENT,
    "content-type": "application/json",
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
}


class HomeDepot(BalanceCheckProvider):
    def __init__(self):
        super().__init__()

        self.website_url = "https://www.homedepot.com/mycheckout/giftcard"
        self.api_endpoint = (
            "https://www.homedepot.com/mcc-checkout/v2/giftcard/balancecheck"
        )
        self.schema = GiftCardSchema(Merchant.HomeDepot)
        self.num_runs = 0
        self.max_workers = 1  # Cannot run multithreaded, IP limited

    def scrape(self, **kwargs):
        logger.info("Solving reCAPTCHA (~30s)")

        captcha_solver = CaptchaSolver(api_key=config.ANTI_CAPTCHA_KEY)

        # Site key obtained from: https://www.homedepot.com/mycheckout/assets/react/giftcard.bundle.1.2302.0.js
        captcha_resp = captcha_solver.solve_recaptcha(
            self.website_url, "6LfEHBkTAAAAAHX6YgeUw9x1Sutr7EzhMdpbIfWJ"
        )

        if captcha_resp["errorId"] != 0:
            raise RuntimeError(
                f"Unable to solve reCAPTCHA ({captcha_resp['errorDescription']})"
            )

        payload = {
            "GiftCardsRequest": {
                "cardNumber": kwargs["card_number"],
                "pinNumber": kwargs["pin"],
                "reCaptcha": captcha_resp["solution"]["gRecaptchaResponse"],
            }
        }

        logger.info("Fetching balance from API")

        try:
            resp = requests.post(self.api_endpoint, json=payload, headers=HEADERS)

            if resp.status_code != 200:
                raise RuntimeError(
                    f"Invalid API response (status code {resp.status_code})"
                )

            result = deep_get(resp.json(), "giftCards.giftCard")
            if result is None:
                raise RuntimeError(
                    f"Invalid API response: unable to find giftCard key in JSON response"
                )

            err_code = deep_get(result, "errorCode")
            if err_code:
                err_desc = deep_get(result, "description")
                raise RuntimeError(
                    f"Failed to retrieve balance from API: {err_desc} ({err_code})"
                )

            initial_balance = deep_get(result, "originalAmount")
            avail_balance = deep_get(result, "availableAmount")

            logger.info(f"Success! Card balance: {avail_balance}")

            return {
                "initial_balance": initial_balance,
                "available_balance": avail_balance,
            }
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error on API post: {e}")
        except JSONDecodeError:
            raise RuntimeError("Failed to parse API response as JSON")

    def check_balance(self, **kwargs):
        if self.validate(kwargs):
            logger.info(f"Checking balance for card: {kwargs['card_number']}")

            return self.scrape(card_number=kwargs["card_number"], pin=kwargs["pin"])
