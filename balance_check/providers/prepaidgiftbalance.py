import time
import base64
import chromedriver_binary
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from balance_check import logger, config
from balance_check.utils.captcha import CaptchaSolver
from balance_check.providers import BalanceCheckProvider
from balance_check.validators.credit_card import Issuer, CreditCardSchema


class PrepaidGiftBalance(BalanceCheckProvider):
    def __init__(self):
        super().__init__()

        self.website_url = "https://www.prepaidgiftbalance.com"
        self.schema = CreditCardSchema([Issuer.Visa, Issuer.MasterCard], exp_date=False)

    def scrape(self, fields):
        # Open Selenium browser
        browser = webdriver.Chrome()
        browser.set_window_size(600, 800)

        logger.info("Fetching balance check page")
        browser.get(self.website_url)

        try:
            form = browser.find_elements_by_tag_name("form")[1]
        except (NoSuchElementException, IndexError):
            raise RuntimeError("Unable to find login form on page")

        logger.info("Filling login form 1/2")
        try:
            form.find_element_by_name("accountNumber").send_keys(
                fields["accountNumber"]
            )
            time.sleep(1)
        except NoSuchElementException:
            browser.close()
            raise RuntimeError(f"Unable to find 'accountNumber' field on page")

        # Click continue button
        form.find_element_by_css_selector("input[type='submit']").click()

        # Wait for page to load
        try:
            WebDriverWait(browser, 3).until(
                EC.presence_of_element_located((By.ID, "login-form"))
            )
        except TimeoutException:
            browser.close()
            raise RuntimeError("Login page took too long to load")

        try:
            form = browser.find_element_by_id("login-form")
        except NoSuchElementException:
            browser.close()
            raise RuntimeError("Unable to find login form on page")

        logger.info("Solving CAPTCHA (~10s)")

        # Take a screenshot of the CAPTCHA image and crop
        captcha_img = Image.open(BytesIO(browser.get_screenshot_as_png()))
        captcha_img = captcha_img.crop(box=(124, 408, 428, 512))

        # Export CAPTCHA image as base64'd PNG
        img_buffer = BytesIO()
        captcha_img.save(img_buffer, format="PNG")
        captcha_b64 = base64.b64encode(img_buffer.getvalue()).decode("utf-8")

        captcha_solver = CaptchaSolver(api_key=config.ANTI_CAPTCHA_KEY)
        captcha = captcha_solver.solve_image_b64(captcha_b64)
        if captcha["errorId"] != 0:
            browser.close()
            raise RuntimeError(
                "Unable to solve CAPTCHA ({})".format(captcha["errorDescription"])
            )

        logger.info("Filling login form 2/2")
        try:
            form.find_element_by_name("cv2").send_keys(fields["cv2"])
            time.sleep(1)
        except NoSuchElementException:
            browser.close()
            raise RuntimeError("Unable to find 'cv2' field on page")

        try:
            form.find_element_by_id(
                "_MultiStageFSVpasswordloginresponsive_WAR_cardportalresponsive_captchaText"
            ).send_keys(captcha["solution"]["text"])
            time.sleep(1)
        except NoSuchElementException:
            browser.close()
            raise RuntimeError("Unable to find CAPTCHA field on page")

        # Click continue button
        form.find_element_by_css_selector("input[type='submit']").click()

        # Wait for page to load
        try:
            WebDriverWait(browser, 3).until(
                EC.presence_of_element_located((By.ID, "cardBalanceInfo"))
            )
        except TimeoutException:
            browser.close()
            raise RuntimeError("Balance page took too long to load")

        logger.info("Obtaining card information")
        try:
            avail_balance = browser.find_element_by_class_name("cardBalanceText").text
        except NoSuchElementException:
            browser.close()
            raise RuntimeError("Could not find available card balance")

        browser.close()
        logger.info(f"Success! Card balance: {avail_balance}")

        return {"initial_balance": None, "available_balance": avail_balance}

    def check_balance(self, **kwargs):
        if self.validate(kwargs):
            logger.info("Checking balance for card: {}".format(kwargs["card_number"]))

            return self.scrape(
                {"accountNumber": kwargs["card_number"], "cv2": kwargs["cvv"]}
            )
