import sys
import csv
from os import path
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
|------------------|-----------|----------|-----|
| 4111111111111111 | 12        | 24       | 999 |
-------------------------------------------------

If you find this tool useful, consider buying a coffee for the author:
https://stevenmirabito.com/kudos""".format(
            providers_help
        ),
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s {}".format(version.__version__),
    )
    parser.add_argument(
        "provider",
        metavar="PROVIDER",
        type=str.lower,
        help="Name of balance check provider",
    )
    parser.add_argument(
        "input", metavar="INPUT_CSV", type=str, help="Path to input CSV"
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="OUTPUT_CSV",
        type=str,
        help=(
            "Path to output CSV (optional; default:"
            "add/overwrite\nbalance columns on input CSV)"
        ),
    )

    args = parser.parse_args()

    in_filename = path.abspath(args.input)
    out_filename = in_filename
    if args.output:
        # Separate output path specified
        out_filename = path.abspath(args.output)

    if args.provider not in providers:
        logger.fatal("Unknown provider: '{}'".format(args.provider))
        sys.exit(1)

    provider = providers[args.provider]
    futures = {}
    results = []
    retries = {}

    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
        try:
            with open(in_filename, newline="") as input_csv:
                reader = csv.DictReader(input_csv)

                for row in reader:
                    # Add the card details to the result
                    results.append(row)
                    idx = len(results) - 1

                    # Schedule balance check
                    future = executor.submit(provider.check_balance, **row)
                    futures[future] = idx
        except (OSError, IOError) as err:
            logger.fatal("Unable to open input file '{}': {}".format(in_filename, err))
            sys.exit(1)
        except Exception as e:
            logger.fatal("Unexpected error: {}".format(e))
            sys.exit(1)

        # While there are still tasks queued, jump back in (handles retries)
        while futures:
            # Update progress bar as tasks complete
            for future in tqdm(as_completed(futures), total=len(futures), leave=False):
                idx = futures.pop(future)

                try:
                    balance_info = future.result()
                except Exception as e:
                    # Log the first column value as an ID (usually card number)
                    card_id = next(iter(results[idx].values()))

                    # Attempt to schedule retry
                    if idx in retries:
                        retries[idx] += 1
                        if retries[idx] > config.RETRY_TIMES:
                            # Out of retries, permanent failure
                            logger.error(
                                "Failed to balance check {} (out of retries). Last error: {}".format(
                                    card_id, e
                                )
                            )
                    else:
                        retries[idx] = 1

                    logger.warning(
                        "RETRY {}/{}: Failed to balance check {}, retrying. Error: {}".format(
                            retries[idx], config.RETRY_TIMES, card_id, e
                        )
                    )

                    future = executor.submit(provider.check_balance, **results[idx])
                    futures[future] = idx
                else:
                    # Combine original card details with balance information
                    results[idx] = dict(results[idx], **balance_info)

    try:
        with open(out_filename, "w", newline="") as output_csv:
            logger.info("Writing output CSV...")

            fieldnames = results[0].keys()
            writer = csv.DictWriter(output_csv, fieldnames=fieldnames)
            writer.writeheader()

            for row in results:
                writer.writerow(row)

            logger.info("Output written to: {}".format(out_filename))
    except (OSError, IOError) as err:
        logger.fatal("Unable to open output file '{}': {}".format(in_filename, err))
        sys.exit(1)
    except Exception as e:
        logger.fatal("Unexpected error: {}".format(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
