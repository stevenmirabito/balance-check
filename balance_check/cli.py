import sys
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from argparse import ArgumentParser, RawTextHelpFormatter
from tqdm import tqdm
from balance_check import logger, config
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
        reader = csv.DictReader(input_csv)

        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            futures = {}

            for row in reader:
                provider = row.pop('provider', None)

                if not provider:
                    logger.error("You must specify a provider for each card. See usage.")
                    sys.exit(1)

                if provider not in providers:
                    logger.warning("Unknown provider: '{}', skipping".format(row["provider"]))
                    continue

                future = executor.submit(providers[provider].check_balance, **row)
                futures[future] = next(iter(row.values()))  # First column value, usually card number

            # Update progress bar as tasks complete
            for future in tqdm(as_completed(futures), total=len(futures)):
                card_id = futures[future]

                try:
                    result = future.result()
                except Exception as e:
                    logger.error("Failed to balance check {}: {}".format(card_id, e))
                else:
                    # TODO: Output CSV
                    print(result)


if __name__ == "__main__":
    main()
