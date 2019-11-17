import colorlog
from typing import Mapping
from balance_check.version import __version__

logger = colorlog.getLogger()

from balance_check.provider import BalanceCheckProvider
from balance_check.providers import *

# Instantiate each provider module and populate the available providers
providers: Mapping[str, BalanceCheckProvider] = {
    cls.__name__.lower(): cls() for cls in BalanceCheckProvider.__subclasses__()
}
