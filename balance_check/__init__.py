import colorlog
from balance_check import config
from balance_check.utils.logging import configure_logger
from balance_check.version import __version__

logger = colorlog.getLogger()
configure_logger(logger)
