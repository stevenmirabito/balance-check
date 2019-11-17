import sys
import csv
from os import path
from concurrent.futures import ThreadPoolExecutor, as_completed
from argparse import ArgumentParser, RawTextHelpFormatter
from tqdm import tqdm
from balance_check import __version__, logger, config
from balance_check.providers import providers


def main():
    providers_help = "\n".join(["  - {}".format(p_name) for p_name in providers.keys()])

    parser = ArgumentParser(
        formatter_class=RawTextHelpFormatter,
        description=f"""Check gift card balances for a variety of providers.

    Supported providers:
    {providers_help}

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
    https://stevenmirabito.com/kudos""",
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "provider",
        metavar="PROVIDER",
        type=str.lower,
        help="Name of balance check provider",
    )

    parser.add_argument(
        "input", metavar="INPUT_CSV", type=str, help="Path to input CSV",
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
    out_filename = in_filename if not args.output else path.abspath(args.output)

    if args.provider not in providers:
        logger.fatal(f"Unknown provider: '{args.provider}'")
        sys.exit(1)

    provider = providers[args.provider]
    max_workers = (
        provider.max_workers if hasattr(provider, "max_workers") else config.MAX_WORKERS
    )
    provider_allows_chunks = True if hasattr(provider, "max_simultaneous") else False
    futures = {}
    results = []
    retries = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        try:
            with open(in_filename, newline="") as input_csv:
                reader = csv.DictReader(input_csv)
                _chunk = []
                for i, card_data in enumerate(reader):
                    # Add the card details to the result
                    results.append(card_data)
                    # Some balance checkers accept multiple cards so prepare to send chunks
                    # !! NEEDS WORK, UNFINISHED
                    if provider_allows_chunks:
                        _chunk.append(card_data)
                        if (
                                i + 1
                        ) % provider.max_simultaneous:  # If end of chunk, send to schedule...
                            # Schedule balance check
                            future = executor.submit(provider.check_balance, _chunk)
                            futures[future] = i
                            _chunk = []  # Clear chunk at end
                    else:
                        future = executor.submit(provider.check_balance, **card_data)
                        futures[future] = i
            # Done reading input file and scheduling
            logger.info(f"Read {len(results)} cards from file '{in_filename}'")
        except (OSError, IOError) as err:
            logger.fatal(f"Unable to open input file '{in_filename}': {err}")
            sys.exit(1)
        except Exception as e:
            logger.fatal(f"Unexpected error: {e}")
            sys.exit(1)

        # While there are still tasks queued, jump back in (handles retries)
        while futures:
            # Update progress bar as tasks complete
            for future in tqdm(as_completed(futures), total=len(futures), leave=False):
                idx = futures.pop(future)

                try:
                    balance_info = future.result()

                    # !! NEEDS WORK, UNFINISHED
                    if provider_allows_chunks:
                        # List of balances from chunk of cards returned
                        for i, balance_info in enumerate(balances_info):
                            results[idx] = dict(results[idx], **balance_info)
                            # If not on last cards balance info...
                            if len(balance_info) - 1 != i:
                                idx += 1
                    else:
                        # Single balance returned
                        results[idx] = dict(results[idx], **balance_info)
                except Exception as e:
                    # Log the first column value as an ID (usually card number)
                    card_id = next(iter(results[idx].values()))

                    # Attempt to schedule retry
                    if idx not in retries:
                        # First retry
                        retries[idx] = 1

                    # Out of retries?
                    if retries[idx] >= config.RETRY_TIMES:
                        logger.error(
                            f"Failed to balance check {card_id} (out of retries). Last error: {e}"
                        )
                        continue

                    # explicit error report
                    # executor.submit(logger.error, "error occurred", exc_info=sys.exc_info())
                    logger.warning(
                        "RETRY {}/{}: Failed to balance check {}, will retry later. Error: {}".format(
                            retries[idx], config.RETRY_TIMES, card_id, e
                        )
                    )
                    # Schedule the retry and increase retry counter
                    future = executor.submit(provider.check_balance, **results[idx])
                    futures[future] = idx
                    retries[idx] += 1

    try:
        with open(out_filename, "w", newline="") as output_csv:
            logger.info(f"Writing CSV output to {out_filename}...")

            fieldnames = results[0].keys()
            writer = csv.DictWriter(output_csv, fieldnames=fieldnames)
            writer.writeheader()

            for row in results:
                writer.writerow(row)

            logger.info(f"Output written to: {out_filename}")
    except (OSError, IOError) as err:
        logger.fatal(f"Unable to open output file '{in_filename}': {err}")
        sys.exit(1)
    except Exception as e:
        logger.fatal(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
