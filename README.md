# CoinGlass Coin Markets API

Run a tiny REST API for CoinGlass coin market metrics, powered by the Apify Actor:

https://apify.com/api_merge/coinglass-coin-markets

This project is for developers who want a simple endpoint like:

```text
GET /markets?exchange=all_exchanges&page=1
```

Use it to fetch market data such as price, market cap, open interest, funding-rate averages, volume changes, long/short ratios, and liquidation totals as clean JSON.

## Run the API

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn app.main:app --reload
```

Open the interactive docs:

```text
http://127.0.0.1:8000/docs
```

## Call the API

Send your Apify token with the request:

```bash
curl "http://127.0.0.1:8000/markets?exchange=all_exchanges&page=1" \
  -H "Authorization: Bearer apify_api_your_token_here"
```

Filter by specific exchanges:

```bash
curl "http://127.0.0.1:8000/markets?exchange=Binance&exchange=Bybit&page=1" \
  -H "Authorization: Bearer apify_api_your_token_here"
```

Response shape:

```json
{
  "success": true,
  "actor": "api_merge/coinglass-coin-markets",
  "runId": "abc123",
  "datasetId": "def456",
  "input": {
    "exchange": ["Binance", "Bybit"],
    "page": 1
  },
  "data": {
    "success": true,
    "message": "Coin markets data fetched successfully.",
    "exchange": ["Binance", "Bybit"],
    "page": 1,
    "totalCount": 971,
    "markets": [
      {
        "symbol": "BTC",
        "current_price": 84773.6,
        "avg_funding_rate_by_oi": 0.00196,
        "avg_funding_rate_by_vol": 0.002647,
        "market_cap_usd": 1683310500117.051,
        "open_interest_usd": 55002072334.9376,
        "price_change_percent_24h": 1.06,
        "long_short_ratio_24h": 1.0313,
        "liquidation_usd_24h": 27519292.973646
      }
    ]
  }
}
```

## Optional: use .env

If you do not want to send the token in every request:

```bash
cp .env.example .env
```

Edit `.env`:

```env
APIFY_TOKEN=apify_api_your_real_token_here
EXCHANGE=all_exchanges
PAGE=1
```

Then call the API without the `Authorization` header:

```bash
curl "http://127.0.0.1:8000/markets?exchange=Kraken&page=1"
```

Keep `.env` private. It is ignored by Git.

## POST example

```bash
curl -X POST "http://127.0.0.1:8000/markets" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer apify_api_your_token_here" \
  -d '{"exchange":["Binance","Bybit"],"page":1}'
```

## Input

| Field | Required | Example | Description |
| --- | --- | --- | --- |
| `exchange` | Yes | `["all_exchanges"]` | Exchange filter. Use `all_exchanges` or one or more supported exchanges. |
| `page` | Yes | `1` | Result page number. Each page returns up to 20 markets. If `0` is provided, the API uses page `1`. |

Supported exchanges:

```text
all_exchanges, Binance, Bybit, OKX, Crypto.com, CoinEx, CME, Deribit, Bitfinex,
dYdX, Bitmex, HTX, Kraken, Bitget, BingX, Gate, KuCoin, WhiteBIT, MEXC,
Bitunix, Hyperliquid, Coinbase
```

## Python script

You can also run the Actor directly from a Python script:

```bash
python examples/run_markets.py
```

The script asks for your Apify token in a hidden prompt, starts the Actor, prints the dataset result, and saves it to `result.json`.

Override the input:

```bash
python examples/run_markets.py --exchange Binance --exchange Bybit --page 1
```

Comma-separated values also work:

```bash
python examples/run_markets.py --exchange Binance,Bybit --page 2
```

## Get an Apify token

1. Open Apify Console.
2. Go to **API & Integrations**.
3. Copy or create an API token.
4. Use it in the `Authorization` header, paste it into the script prompt, or save it in `.env` as `APIFY_TOKEN`.

## What you can build

- Crypto market dashboards
- Open interest and funding-rate monitors
- Exchange comparison tools
- Trading research notebooks
- Scheduled market snapshots through Apify

## Deployment note

If you deploy this API publicly with your own `APIFY_TOKEN` in `.env`, protect the service with your own auth, rate limits, or billing. Otherwise, public users can consume your Apify account.

## Official Apify Actor

Use the hosted Actor here:

https://apify.com/api_merge/coinglass-coin-markets

## Files

```text
.
├── .env.example
├── README.md
├── requirements.txt
├── app
│   ├── __init__.py
│   └── main.py
└── examples
    ├── fastapi.md
    ├── python.md
    └── run_markets.py
```
