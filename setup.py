import os
from setuptools import setup, find_packages

# this sets __version__
# via: http://stackoverflow.com/a/7071358/87207
# and: http://stackoverflow.com/a/2073599/87207
with open(os.path.join("balance_check", "version.py"), "rb") as f:
    exec(f.read())

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="balance_check",
    version=__version__,
    description="Check gift card balances for a variety of providers",
    url="http://github.com/stevenmirabito/balance_check",
    author="Steven Mirabito",
    author_email="steven@stevenmirabito.com",
    license="MIT",
    packages=find_packages(),
    entry_points={"console_scripts": ["balance-check=balance_check.__main__:main"]},
    install_requires=requirements,
)
