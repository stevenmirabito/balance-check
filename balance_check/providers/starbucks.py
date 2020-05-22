import asyncio
import pyppeteer
from balance_check import logger
from balance_check.provider import BalanceCheckProvider
from balance_check.validators.gift_card import Merchant, GiftCardSchema


class Starbucks(BalanceCheckProvider):
    def __init__(self):
        super().__init__()

        self.website_url = "https://www.starbucks.com/card"
        self.schema = GiftCardSchema(Merchant.Starbucks)

    async def scrape(self, fields):
        browser = await pyppeteer.launch(
            handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False
        )
        page = await browser.newPage()

        logger.info("Fetching balance check page")
        await page.goto(self.website_url)

        logger.info("Filling balance check form")
        await page.type("#Card_Number", fields["card_number"])
        await page.type("#Card_Pin", fields["pin"])

        logger.info("Requesting balance")
        await page.click("#CheckBalance button")
        await page.waitForSelector(".fetch_balance_value", {"timeout": 10000})

        avail_balance = await page.querySelectorEval(
            ".fetch_balance_value", "(node => node.innerText)"
        )

        logger.info("Success! Card balance: {}".format(avail_balance))

        return {"available_balance": avail_balance}

    def check_balance(self, **kwargs):
        if self.validate(kwargs):
            logger.info("Checking balance for card: {}".format(kwargs["card_number"]))

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            return loop.run_until_complete(
                self.scrape(
                    {"card_number": kwargs["card_number"], "pin": kwargs["pin"],}
                )
            )
