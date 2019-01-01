import re
from enum import Enum


class Merchant(Enum):
    GameStop = 'GameStop'


merchant_regex = {
    Merchant.GameStop: re.compile('^636491[0-9]{13}$')
}


def GiftCardSchema(merchant):
    def merchant_check(field, value, error):
        if not merchant_regex[merchant].match(value):
            error(field, "invalid card number for merchant: {}".format(merchant))

    return {
        "card_number": {
            "required": True,
            "type": "string",
            "empty": False,
            "validator": [
                merchant_check
            ]
        },
        "pin": {
            "required": True,
            "type": "string",
            "minlength": 4,
            "maxlength": 8,
            "empty": False
        }
    }
