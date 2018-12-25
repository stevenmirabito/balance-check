import sys
from typing import Mapping
from cerberus import Validator


class BalanceCheckProvider:
    def __init__(self):
        self.schema = None

    def validate(self, args):
        if self.schema:
            validator = Validator(self.schema)
            if not validator.validate(args):
                print("Invalid data provided:", file=sys.stderr)
                for field, errors in validator.errors.items():
                    print("- {}:".format(field), end="", file=sys.stderr)

                    if len(errors) == 1:
                        print(" {}".format(errors[0]), file=sys.stderr)
                    elif len(errors) > 1:
                        print("", file=sys.stderr)
                        for error in errors:
                            print("  - {}".format(error), file=sys.stderr)

                return False

        return True

    def check_balance(self, **kwargs):
        raise NotImplementedError("Implement in subclass")


from balance_check.providers.blackhawk import Blackhawk
from balance_check.providers.spafinder import Spafinder

providers: Mapping[str, BalanceCheckProvider] = {
    'Blackhawk': Blackhawk(),
    'Spafinder': Spafinder()
}
