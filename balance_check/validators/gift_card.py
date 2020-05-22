import re
from enum import Enum


class Merchant(Enum):
    GameStop = "GameStop"
    BestBuy = "Best Buy"
    HomeDepot = "The Home Depot"
    Nike = "Nike"
    Southwest = "Southwest Airlines"
    GuitarCenter = "Guitar Center"
    Starbucks = "Starbucks"


merchant_regex = {
    Merchant.GameStop: re.compile("^636491[0-9]{13}$"),
    # Merchant.Sears: re.compile('^[0-9]{16}$'), # TODO : refine
    # Merchant.Target: re.compile('^04(9|1)[0-9]{12}$'),
    # Merchant.Lowes: re.compile('^60064917[0-9]{11}$'),
    Merchant.BestBuy: re.compile("^(61|60)[0-9]{14}$"),
    Merchant.Nike: re.compile("^606010[0-9]{13}"),
    # Merchant.Lowes: TODO
    Merchant.HomeDepot: re.compile("^9\d{22}"),
    Merchant.GuitarCenter: re.compile("^61(53|64)[0-9]{12}"),
    Merchant.Starbucks: re.compile("^61\d{14}"),
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
            "check_with": merchant_check,
        },
        "pin": {
            "required": True,
            "type": "string",
            "minlength": 4,
            "maxlength": 8,
            "empty": False,
        },
    }
