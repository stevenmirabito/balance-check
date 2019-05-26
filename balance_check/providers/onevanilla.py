import time
import chromedriver_binary
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from balance_check import logger
from balance_check.providers import BalanceCheckProvider
from balance_check.validators.credit_card import Issuer, CreditCardSchema


class OneVanilla(BalanceCheckProvider):
    def __init__(self):
        super().__init__()

        self.website_url = "https://www.onevanilla.com"
        self.schema = CreditCardSchema([Issuer.Visa])

    def scrape(self, fields):
        # Open Selenium browser
        browser = webdriver.Chrome()

        logger.info("Fetching balance check page")
        browser.get(self.website_url)

        logger.info("Filling balance check form")
        for field, val in fields.items():
            try:
                browser.find_element_by_id(field).send_keys(val)
                time.sleep(1)
            except NoSuchElementException:
                browser.close()
                raise RuntimeError(f"Unable to find '{field}' field on page")

        # Click submit button
        browser.find_element_by_id("brandLoginForm_button").click()

        # Wait for page to load
        try:
            WebDriverWait(browser, 3).until(
                EC.presence_of_element_located((By.ID, "Avlbal"))
            )
        except TimeoutException:
            browser.close()
            raise RuntimeError("Balance page took too long to load")

        logger.info("Obtaining card information")
        try:
            avail_balance = browser.find_element_by_id("Avlbal").text
        except NoSuchElementException:
            browser.close()
            raise RuntimeError("Could not find available card balance")

        try:
            initial_balance = (
                browser.find_element_by_class_name("rightSide")
                .find_element_by_tag_name("span")
                .text
            )
        except NoSuchElementException:
            browser.close()
            raise RuntimeError("Could not find initial card balance")

        browser.close()
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
