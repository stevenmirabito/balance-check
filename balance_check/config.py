from os import environ as env

ANTI_CAPTCHA_KEY = env.get("ANTI_CAPTCHA_KEY", "")
MAX_WORKERS = int(env.get("MAX_WORKERS", "5"))
RETRY_TIMES = int(env.get("RETRY_TIMES", "3"))
USER_AGENT = env.get("USER_AGENT", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:64.0) Gecko/20100101 Firefox/64.0")
