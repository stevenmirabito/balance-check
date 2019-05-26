import colorlog
from balance_check import config
from balance_check.utils.logging import configure_logger

logger = colorlog.getLogger()
configure_logger(logger)
