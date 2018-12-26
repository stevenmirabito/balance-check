import sys
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from argparse import ArgumentParser, RawTextHelpFormatter
from tqdm import tqdm
from balance_check import logger, config, version
from balance_check.providers import providers


def main():
    providers_help = "\n".join(["  - {}".format(p_name) for p_name in providers.keys()])

    parser = ArgumentParser(
        formatter_class=RawTextHelpFormatter,
        description="""Check gift card balances for a variety of providers.
        
Supported providers:
{}

Requires an Anti-CAPTCHA API key for providers with CAPTCHAs.
Get one here: https://anti-captcha.com
Configure your key by setting the ANTI_CAPTCHA_KEY environment variable.

Your INPUT_CSV should be formatted as follows:
  - A header row is required
  - Each column should contain a parameter required by
    the specified provider

Example (for the 'blackhawk' provider):
-------------------------------------------------
| card_number      | exp_month | exp_year | cvv |
|------------------------------|----------|-----|
| 4111111111111111 | 12        | 24       | 999 |
-------------------------------------------------""".format(providers_help))

    parser.add_argument("-v", "--version", action="version", version="%(prog)s {}".format(version.__version__))
    parser.add_argument("provider", metavar="PROVIDER", type=str.lower,
                        help="Name of balance check provider")
    parser.add_argument("input", metavar="INPUT_CSV", type=str,
                        help="Path to input CSV")
    parser.add_argument("-o", "--output", metavar="OUTPUT_CSV", type=str,
                        help="Path to output CSV (optional; default: add/overwrite\n'balance' column on input "
                             "spreadsheet)")

    args = parser.parse_args()

    if args.provider not in providers:
        logger.fatal("Unknown provider: '{}'".format(args.provider))
        sys.exit(1)

    provider = providers[args.provider]

    with open(args.input, newline="") as input_csv:
        reader = csv.DictReader(input_csv)

        with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            futures = {}

            for row in reader:
                future = executor.submit(provider.check_balance, **row)
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
