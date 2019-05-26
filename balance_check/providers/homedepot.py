import requests
from balance_check import logger, config
from balance_check.utils.captcha import CaptchaSolver
from balance_check.providers import BalanceCheckProvider
from balance_check.validators.gift_card import Merchant, GiftCardSchema
from fake_useragent import UserAgent


# TODO - not working
#


class HomeDepot(BalanceCheckProvider):
    def __init__(self):
        super().__init__()

        self.website_url = "https://secure2.homedepot.com/mycheckout/giftcard"
        self.api_endpoint = (
            "https://secure2.homedepot.com/mcc-checkout/v2/giftcard/balancecheck"
        )
        self.schema = GiftCardSchema(Merchant.HomeDepot)
        self.num_runs = 0
        self.ua = UserAgent()
        self.max_workers = 1  # Cannot run multithreaded, IP limited

    def scrape(self, **kwargs):
        captcha_solver = CaptchaSolver(api_key=config.ANTI_CAPTCHA_KEY)

        # Site key gathered from https://secure2.homedepot.com/mycheckout/assets/react/giftcard.bundle.js?v=v1.2040.2
        # 6LfEHBkTAAAAAHX6YgeUw9x1Sutr7EzhMdpbIfWJ and 6Le3GRkTAAAAAPpXON0jcJCLrYZnm-ZqyLhbCLbX

        captcha_resp = captcha_solver.solve_recaptcha(
            self.website_url, "6LfEHBkTAAAAAHX6YgeUw9x1Sutr7EzhMdpbIfWJ"
        )
        if captcha_resp["errorId"] != 0:
            raise RuntimeError(
                f"Unable to solve reCAPTCHA ({captcha_resp['errorDescription']})"
            )

        # Begin API request
        session = requests.Session()
        # Get balance check page to grab cookies
        session.get(self.website_url)

        session.headers.update(
            {
                "origin": "https://secure2.homedepot.com",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
                "content-type": "application/json",
                "accept": "application/json, text/plain, */*",
                "referer": "https://secure2.homedepot.com/mycheckout/giftcard",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "en-US,en;q=0.9",
                # 'cookie': "HD_DC=origin; check=true; _abck=3D7AEA27759869A787304AD8C0B93D1C17C532E781200000EB2DB15ACADB6E34~0~Ie8mODWyYhnd9Jka+w+AC39XvfEAlhz78nuYgOCT8so=~-1~-1; AMCVS_F6421253512D2C100A490D45%40AdobeOrg=1; thda.u=5f480787-7953-8e2e-14c3-0b96cfd48040; thda.s=054d35ff-11c7-6b16-75cd-bbcd2d48c17b; RES_TRACKINGID=85286815566469932; ftr_ncd=6; thda.m=81084504873679911179154344636083105898; LPVID=Q5OGUwNTliM2EzY2NmM2Yw; cto_lwid=2dc94469-69f2-49af-886c-69251e0ee8da; THD_FORCE_LOC=1; THD_MCC_ID=6f1d76fc-8b8e-45be-97ea-9c061f79f851; cart_activity=8777201b-f4c7-4ccc-8e3e-428c62d3c730; WORKFLOW=LOC_HISTORY_BY_IP; THD_INTERNAL=0; og_session_id=379dc8f09a4311e7806bbc764e106cf4.731928.1538275068; IR_gbd=homedepot.com; ecrSessionId=6ED9C65DD7DE929C82CAEB9D58E38D71; THD_USER=\"eyJzdm9jQ3VzdG9tZXJBY2NvdW50SWQiOiIwM0VEMjFBQ0JDNTgzNTkwMFMiLCJsb2dvbklkIjoiaG9tZWRlcG90QGJpa2VtYW5kYW4uY29tIiwidXNlcklkIjoiMDUxM0UyMTkyOTIxRTY5MTBVIiwiY3VzdG9tZXJUeXBlIjoiQjJDIn0=\"; THD_USER_SESSION=AQIC5wM2LY4SfcxJD0XieCwTVsVkLiR7a2oDQMG6d90y3To.*AAJTSQACMDIAAlNLABM2MzI5MDk2NzEyMTU1OTY3NjQ4AAJTMQACMDY.*; THD_CACHE_NAV_PERSIST=\"\"; THD_CACHE_NAV_SESSION=C20%7E0_%7EC20_EXP%7E_%7EC22%7E641_%7EC22_EXP%7E_%7EC26%7EP_REP_PRC_MODE%7C0_%7EC26_EXP%7E; ak_bmsc=C6D4C7801E4881DEBB1E03DF88F8F1CF17C532D4FC2700009D15395C49757425~plfpoGCv+yaNOcuoWld8wCQ3wGC2Yh+Dl/XvPv5aTAd9s7O3guYCefrdJKkL4e+oVw8WlPV3onzF+qQyqCQ0fQrP9dWjPPDzi2FDN8mCAQ4GC4752Ucds9YyV7Vb8oOB4KiekG+BZiyaPSse/+QTkx7VA+q2wy5Kc7bTXGsK1BJKZ8nZf8sBcVVuypxX8ZJjK3x4h6ChD396S6SWGu9KOR5Gws+4xT6nE1xBZfzVt/pSA=; bm_sz=993B9150C6357D1453561ED8533D948C~QAAQ1DLFF1EGQC9oAQAAWW78Pvljdn9YU6uwR/wj13nNtKbJAd1tz/XtkSB4D0GzZ0sB6xr9f6lmedf6cPJTA7GFYjVV7H4/3px/zWyNeY73uc1wGoIs4b2EDW9ft+53/wIzZavesl7pmzhBMiCA5GKqJ4WFF9oO4+EP3gtOxVKIKMDjVP8J/UAn2a3coAOZ0zs=; THD_SESSION=; AMCV_F6421253512D2C100A490D45%40AdobeOrg=-894706358%7CMCIDTS%7C17908%7CMCMID%7C81084504873679911179154344636083105898%7CMCAID%7CNONE%7CMCOPTOUT-1547252157s%7CNONE%7CvVersion%7C2.3.0; THD_PERSIST=C4%3D641%2BRohnert%20Pk%20-%20Rohnert%20Park%2C%20CA%2B%3A%3BC4_EXP%3D1578780959%3A%3BC24%3D94928%3A%3BC24_EXP%3D1578780959%3A%3BC34%3D32.1%3A%3BC34_EXP%3D1547331358%3A%3BC39%3D1%3B7%3A00-20%3A00%3B2%3B6%3A00-22%3A00%3B3%3B6%3A00-22%3A00%3B4%3B6%3A00-22%3A00%3B5%3B6%3A00-22%3A00%3B6%3B6%3A00-22%3A00%3B7%3B6%3A00-22%3A00%3A%3BC39_EXP%3D1547248559; ResonanceSegment=1; signInBubble=true; s_dfa=homedepotprod%2Chomedepotglobaldev; ats-cid-AM-141099-sid=46341048; LPSID-31564604=tgZo3ZtbTmaR_Y-e3nvjcQ; bm_mi=21A83C44D89B199539D14330195C2F99~mGutnDw9T1dVaFjCLHwYLZw3kAOjDjotPSLR4WpSqqHiFQpXWyR4sK+9B3XaCHm6PTzxe40CC15/SSfwKqFR69zJ9MNcL+Ikczcr4Mq4STJ8E4DGF8ozcpOICIx7wUHr4bN9S6EoHVGMsDpO6tntSLxWq4i2U3SDGUXpFjyWEHVYJoMil8dK0D1+BduiBRPiryGLnSu00wtXOnXDXIgSEETU/dWSRtwRyDwYSIA02+JU+MGUWuObfgriro9Zd2tl; bm_sv=176F5E5B2FBE5E8295D8CCE4214111A6~lvtdTZIv6RPPE+bbvi5sIhT//R4DBFahLwcKcw/HA61WomPuVKOI4uq9Fr0BJTsx7o1U57Vsw3iSq+JvBAadGMOiQjWILK6R/pWM/LHXLaRQCnWoMbQbe1Is1Zc4ZKe4wStAcGNCCi2+WT4udxpsK3vuYFnaBUlGjr1uTmEGZ/o=; forterToken=2a23633194f246a7871e5c4f3f1546d8_1547247463626_21_UDF43_6; s_pers=%20s_nr%3D1547247468412-Repeat%7C1578783468412%3B%20s_dslv%3D1547247468416%7C1641855468416%3B%20s_dslv_s%3DLess%2520than%25201%2520day%7C1547249268416%3B%20productnum%3D98%7C1549839468424%3B; IR_8154=1547247468480%7C0%7C1547247402943%7C308SnG1k%3Ax6NRl41WlS2czhgUkgycW2FszrdRM0; IR_PI=1538887702311.ypfh9yayldq%7C1547333868480; s_sess=%20stsh%3D%3B%20s_pv_pName%3Dgift%2520card%253Ebalance%2520check%3B%20s_pv_pType%3Dgift%2520card%3B%20s_pv_cmpgn%3D%3B%20s_cc%3Dtrue%3B%20s_sq%3Dhomedepotprod%25252Chomedepotglobaldev%253D%252526c.%252526a.%252526activitymap.%252526page%25253Dgift%25252520card%2525253Ebalance%25252520check%252526link%25253DCheck%25252520Balance%252526region%25253Dapp%252526pageIDType%25253D1%252526.activitymap%252526.a%252526.c%252526pid%25253Dgift%25252520card%2525253Ebalance%25252520check%252526pidt%25253D1%252526oid%25253Dfunctionpr%25252528%25252529%2525257B%2525257D%252526oidt%25253D2%252526ot%25253DSUBMIT%3B",
                "cache-control": "no-cache",
            }
        )

        payload = {
            "GiftCardsRequest": {
                "cardNumber": kwargs["card_number"],
                "pinNumber": kwargs["pin"],
                "reCaptcha": captcha_resp["solution"]["gRecaptchaResponse"],
            }
        }
        logger.info(f"Fetching balance from API")

        try:
            resp = session.post(self.api_endpoint, json=payload, timeout=5)
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error on API post: {e}")
        if resp.status_code != 200:
            raise RuntimeError(
                f"Failed to get valid response from API (status code {resp.status_code})"
            )

        print(resp.text)
        quit()

        # try:
        #     avail_balance = resp.json()["balance"]
        # except:
        #     raise RuntimeError("Could not parse balance from JSON response")

        # logger.info(f"Success! Card balance: {avail_balance}")
        # # TODO: figure out cleaner way to do this, feature in main?
        # self.num_runs += 1
        # # Not sure exactly what sweet spot is but IP blocks at 10 min, 15 min seems good
        # seconds = 3 if self.num_runs % 9 else 60*15+5
        # logger.info(f"Ran {self.num_runs} times. Sleeping {seconds} seconds before trying next...")
        # time.sleep(seconds)

        # return {"balance": avail_balance}

    def check_balance(self, **kwargs):
        if self.validate(kwargs):
            logger.info(f"Checking balance for card: {kwargs['card_number']}")

            return self.scrape(card_number=kwargs["card_number"], pin=kwargs["pin"])
        # else:
        # Invalid
