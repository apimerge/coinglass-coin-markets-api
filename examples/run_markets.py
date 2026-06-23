from __future__ import annotations

import argparse
from getpass import getpass
import json
import os
import sys
from pathlib import Path

from apify_client import ApifyClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"
OUTPUT_FILE = PROJECT_ROOT / "result.json"
ACTOR_ID = "api_merge/coinglass-coin-markets"
SUPPORTED_EXCHANGES = {
    "all_exchanges",
    "Binance",
    "Bybit",
    "OKX",
    "Crypto.com",
    "CoinEx",
    "CME",
    "Deribit",
    "Bitfinex",
    "dYdX",
    "Bitmex",
    "HTX",
    "Kraken",
    "Bitget",
    "BingX",
    "Gate",
    "KuCoin",
    "WhiteBIT",
    "MEXC",
    "Bitunix",
    "Hyperliquid",
    "Coinbase",
}


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]

        os.environ.setdefault(key, value)


def split_exchange_values(values: list[str] | None) -> list[str]:
    if not values:
        return ["all_exchanges"]

    exchanges: list[str] = []
    for value in values:
        exchanges.extend(item.strip() for item in str(value).split(",") if item.strip())

    unique_exchanges = list(dict.fromkeys(exchanges)) or ["all_exchanges"]
    if len(unique_exchanges) > 1 and "all_exchanges" in unique_exchanges:
        unique_exchanges = [exchange for exchange in unique_exchanges if exchange != "all_exchanges"]

    return unique_exchanges


def parse_args() -> argparse.Namespace:
    default_exchanges = split_exchange_values([os.getenv("EXCHANGE", "all_exchanges")])
    parser = argparse.ArgumentParser(
        description="Run the CoinGlass Coin Markets Apify Actor and print the dataset result.",
    )
    parser.add_argument(
        "--exchange",
        action="append",
        default=None,
        help="Exchange filter. Use multiple times or comma-separated values. Default: all_exchanges.",
    )
    parser.add_argument("--page", type=int, default=int(os.getenv("PAGE", "1")))
    args = parser.parse_args()
    args.exchange = split_exchange_values(args.exchange) if args.exchange else default_exchanges
    return args


def get_apify_token() -> str:
    token = os.getenv("APIFY_TOKEN", "").strip()
    if token and not token.startswith("apify_api_your_"):
        return token

    try:
        return getpass("Apify API token: ").strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def validate_exchanges(exchanges: list[str]) -> bool:
    unsupported = [exchange for exchange in exchanges if exchange not in SUPPORTED_EXCHANGES]
    if unsupported:
        print(f"Unsupported exchange: {', '.join(unsupported)}", file=sys.stderr)
        print(f"Supported values: {', '.join(sorted(SUPPORTED_EXCHANGES))}", file=sys.stderr)
        return False

    return True


def get_run_value(run: object, api_key: str, attr_name: str | None = None) -> object:
    if isinstance(run, dict):
        return run.get(api_key) or (run.get(attr_name) if attr_name else None)

    if attr_name and hasattr(run, attr_name):
        return getattr(run, attr_name)

    if hasattr(run, api_key):
        return getattr(run, api_key)

    if hasattr(run, "model_dump"):
        data = run.model_dump(by_alias=True)
        return data.get(api_key) or (data.get(attr_name) if attr_name else None)

    return None


def main() -> int:
    load_env_file(ENV_FILE)
    args = parse_args()

    token = get_apify_token()
    if not token:
        print(
            "Missing Apify token. Paste it at the prompt or set APIFY_TOKEN in .env.",
            file=sys.stderr,
        )
        return 1

    exchanges = split_exchange_values(args.exchange)
    if not validate_exchanges(exchanges):
        return 1

    page = args.page if args.page > 0 else 1
    run_input = {
        "exchange": exchanges,
        "page": page,
    }

    print(f"Running {ACTOR_ID} with input:")
    print(json.dumps(run_input, indent=2))

    client = ApifyClient(token)
    run = client.actor(ACTOR_ID).call(run_input=run_input)

    status = get_run_value(run, "status")
    if status and status != "SUCCEEDED":
        print(f"Actor finished with status: {status}", file=sys.stderr)
        return 1

    dataset_id = get_run_value(run, "defaultDatasetId", "default_dataset_id")
    if not dataset_id:
        print("Actor run did not return a default dataset id.", file=sys.stderr)
        return 1

    items = list(client.dataset(str(dataset_id)).iterate_items())
    if not items:
        print("Actor finished, but the default dataset is empty.", file=sys.stderr)
        return 1

    result = items[0] if len(items) == 1 else items
    OUTPUT_FILE.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nSaved result to {OUTPUT_FILE.name}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

