import sys
import csv
from argparse import ArgumentParser, RawTextHelpFormatter
from tqdm import tqdm
from balance_check import logger
from balance_check.providers import providers


def main():
    parser = ArgumentParser(
        formatter_class=RawTextHelpFormatter,
        description="""Check gift card balances for a variety of providers.

Your INPUT_CSV should be formatted as follows:
  - A header row is required
  - The first column must be 'provider'
  - Subsequent columns should contain the parameters required by
    the specified provider

Example:
--------------------------------------
| provider  | card_number      | ... |
|------------------------------------|
| Blackhawk | 4111111111111111 | ... |
--------------------------------------""")

    parser.add_argument("input", metavar="INPUT_CSV", type=str,
                        help="Path to Input CSV")
    parser.add_argument("-o", "--output", metavar="OUTPUT_CSV", type=str,
                        help="Path to output CSV (optional; default: add/overwrite\n'balance' column on input "
                             "spreadsheet)")

    args = parser.parse_args()

    with open(args.input, newline="") as input_csv:
        # Total number of rows in file, subtracting header row and excluding empty lines
        total = sum(0 if row.strip() == "" else 1 for row in input_csv) - 1
        input_csv.seek(0)

        if total < 1:
            logger.warning("Nothing to do.", file=sys.stderr)
            sys.exit(2)

        reader = csv.DictReader(input_csv)
        for row in tqdm(reader, total=total):
            provider = row.pop('provider', None)

            if not provider:
                logger.error("You must specify a provider for each card. See usage.")
                sys.exit(1)

            if provider not in providers:
                logger.warning("Unknown provider: '{}', skipping".format(row["provider"]))
                continue

            providers[provider].check_balance(**row)
