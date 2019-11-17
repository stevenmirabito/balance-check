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
