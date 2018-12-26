import os
from pkgutil import iter_modules
from importlib import import_module
from typing import Mapping
from cerberus import Validator
from balance_check import logger


class BalanceCheckProvider:
    def __init__(self):
        self.schema = None

    def validate(self, args):
        if self.schema:
            validator = Validator(self.schema)
            if not validator.validate(args):
                msg = "Invalid card data provided:\n"

                for field, errors in validator.errors.items():
                    msg += "- {}:".format(field)

                    if len(errors) == 1:
                        msg += " {}\n".format(errors[0])
                    elif len(errors) > 1:
                        msg += "\n"
                        for error in errors:
                            msg += "  - {}\n".format(error)

                logger.error(msg)
                return False

        return True

    def check_balance(self, **kwargs):
        raise NotImplementedError("Implement in subclass")


# Import all provider modules
for _, name, _ in iter_modules([os.path.dirname(__file__)]):
    import_module("." + name, __package__)

# Instantiate each provider module and populate the available providers
providers: Mapping[str, BalanceCheckProvider] = {
    cls.__name__.lower(): cls() for cls in BalanceCheckProvider.__subclasses__()
}
