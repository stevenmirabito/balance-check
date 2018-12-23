import colorlog
from balance_check import config
from balance_check.utils.logging import configure_logger
from balance_check.utils.captcha import CaptchaSolver

logger = colorlog.getLogger()
configure_logger(logger)

captcha_solver = CaptchaSolver(api_key=config.ANTI_CAPTCHA_KEY)
