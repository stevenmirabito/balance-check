import re
from enum import Enum
from luhn import verify


class Issuer(Enum):
    Visa = "Visa"
    MasterCard = "MasterCard"
    Discover = "Discover"
    Amex = "American Express"


issuer_regex = {
    Issuer.Visa: re.compile("^4[0-9]{12}(?:[0-9]{3})?$"),
    Issuer.MasterCard: re.compile("^5[1-5][0-9]{14}$"),
    Issuer.Discover: re.compile("^6(?:011|5[0-9]{2})[0-9]{12}$"),
    Issuer.Amex: re.compile("^3[47][0-9]{13}$"),
}


def luhn_check(field, value, error):
    if not verify(value):
        error(field, "does not pass Luhn check")


def CreditCardSchema(issuers):
    def issuer_check(field, value, error):
        if not any(issuer_regex[issuer].match(value) for issuer in issuers):
            error(
                field,
                "invalid card number for issuer(s): {}".format(
                    ", ".join([issuer.value for issuer in issuers])
                ),
            )

    return {
        "card_number": {
            "required": True,
            "type": "string",
            "empty": False,
            "validator": [issuer_check, luhn_check],
        },
        "exp_month": {
            "required": True,
            "type": "string",
            "minlength": 2,
            "maxlength": 2,
            "empty": False,
        },
        "exp_year": {
            "required": True,
            "type": "string",
            "minlength": 2,
            "maxlength": 2,
            "empty": False,
        },
        "cvv": {
            "required": True,
            "type": "string",
            "minlength": 3,
            "maxlength": 4,
            "empty": False,
        },
    }
