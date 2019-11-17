<p align="center"><img src="https://img.icons8.com/cotton/128/bank-cards.png" alt="Logo" /></p>

<h2 align="center">Balance Check</h2>

<p align="center">
<a href="https://travis-ci.com/stevenmirabito/balance-check"><img src="https://travis-ci.com/stevenmirabito/balance-check.svg?branch=master" alt="Build Status" /></a>
<a href="https://ci.appveyor.com/project/stevenmirabito/balance-check/branch/master"><img src="https://ci.appveyor.com/api/projects/status/n6odgn7kgq2nadgf/branch/master?svg=true" alt="Build status" /></a>
<a href="https://www.python.org/downloads/release/python-360/"><img src="https://img.shields.io/badge/python-3.7-blue.svg" alt="Python 3.7" /></a>
<a href="https://github.com/stevenmirabito/balance-check/blob/master/LICENSE"><img src="https://img.shields.io/github/license/stevenmirabito/balance-check.svg" alt="License: MIT" /></a>
<a href="https://github.com/ambv/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black" /></a>
</p>

Automation tool for checking the balance of gift cards issued by various providers.

## Supported Providers
- [Blackhawk / Gift Card Mall / Simon / 5Back](https://mygift.giftcardmall.com) - `blackhawk` <sup>CAPTCHA</sup>
- [Spafinder](https://www.spafinder.com/pages/card-balance-inquiry/vpln) - `spafinder` <sup>CAPTCHA</sup>
- [GameStop](https://www.gamestop.com/giftcards/) - `gamestop` <sup>CAPTCHA</sup>
- [Best Buy](https://www.bestbuy.com/gift-card-balance) - `bestbuy`
- [Home Depot](https://www.homedepot.com/mycheckout/giftcard) - `homedepot` <sup>CAPTCHA</sup>

Providers marked with <sup>CAPTCHA</sup> will require an [Anti-CAPTCHA](https://anti-captcha.com) API key.

## Quick Start
Download and extract the appropriate standalone executable file for your operating system from the [releases page](https://github.com/stevenmirabito/balance-check/releases).

### Windows

Open a command prompt and `cd` to the directory where you downloaded the executable, e.g.:

```
cd C:\Users\John\Downloads
```

Or, open the folder in Explorer, hold the `SHIFT` key, and choose "Open Command Prompt Here" from the context menu.

From that command prompt window, run the following to display the full usage message:

```
balance-check.exe -h
```

To configure your Anti-CAPTCHA API key, run the following (replacing `<key>` with your key):

```
set ANTI_CAPTCHA_KEY="<key>"
```

To run a balance check using the `blackhawk` provider using a CSV on your desktop, you might run the following:

```
balance-check.exe blackhawk C:\Users\John\Desktop\cards.csv
```

Instead of typing out the full path to the input CSV, you can also drag-and-drop the CSV into the command prompt window after typing the first part of the command.

### macOS & Linux

Open a terminal (macOS: Applications -> Utilities -> Terminal) and `cd` to the directory where you downloaded the binary, e.g.:

```
cd ~/Downloads
```

From that termal window, run the following to display the full usage message:

```
balance-check -h
```

To configure your Anti-CAPTCHA API key, run the following (replacing `<key>` with your key):

```
export ANTI_CAPTCHA_KEY="<key>"
```

To run a balance check using the `blackhawk` provider using a CSV on your desktop, you might run the following:

```
balance-check blackhawk ~/Desktop/cards.csv
```

## CSV Format

Your input CSV should be formatted as follows:

- Each column should contain a parameter required by the specified provider
- A header row is required and should label each column with the name of the parameter it is defining

Each provider expects a certain set of parameters. In general, a provider supporting a prepaid debit card will expect a `card_number`, `exp_month`, `exp_year`, and `cvv` and a provider supporting a typical third-party gift card will expect a `card_number` and `pin`.

Example (for the `blackhawk` provider):

| card_number      | exp_month | exp_year | cvv |
|------------------|-----------|----------|-----|
| 4111111111111111 | 12        | 24       | 999 |

## Contributing

Contributions of all kinds are welcome!

To get started, install [Python 3.7](https://www.python.org/downloads/release), `pip`, and `virtualenv`.

Clone this repository, set up your virutal environment, and install the dependencies:

```
git clone https://github.com/stevenmirabito/balance-check.git
cd balance-check
virtualenv .venv -p python3
pip install -r requirements.txt
pre-commit install
```

You can invoke the tool by running `python -m balance_check` in place of `balance-check`.

Please fork this repository, push to your fork, and open a pull request to contribute changes.

### Adding a Provider

Providers must implement a uniquely-named subclass of `BalanceCheckProvider` in the `balance_check.providers` module. If your provider has been successfully registered, it will appear in the usage message as a supported provider.

Your provider must implement `check_balance(self, **kwargs)` which will accept a keyword argument for each column in the input spreadsheet. You may optionally define a [Cerberus schema](http://docs.python-cerberus.org/en/stable/validation-rules.html) on `self.schema` and invoke `self.validate` with any fields you would like to validate. This is recommended to ensure your provider will not send requests with bad card data. A built-in schema generator for prepaid cards is provided in `balance_check.validators.credit_card` and convenience functions for solving CAPTCHAs are provided on `balance_check.captcha_solver`.

Notes:

- Do not `print()` inside your provider - instead, import `balance_check.logger` which has been configured to not interfere with the progress bar shown to the user
- If your provider is unable to successfully retrieve the balance for a card, it is safe to simply raise an exception - this will be caught by the application, the user will be shown a formatted message, and the check will be retried.

<hr>

If you find this tool useful, consider [buying a coffee](https://stevenmirabito.com/kudos) for the author.

[Bank Cards icon by Icons8](https://icons8.com/icon/68592/bank-cards)
