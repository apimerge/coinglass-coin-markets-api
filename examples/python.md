# Python Example

Run the CoinGlass Coin Markets Actor from Python and read the JSON result from the default Apify dataset.

```python
from apify_client import ApifyClient

client = ApifyClient("apify_api_your_token_here")

run_input = {
    "exchange": ["all_exchanges"],
    "page": 1,
}

run = client.actor("api_merge/coinglass-coin-markets").call(run_input=run_input)
dataset_id = run.default_dataset_id
items = list(client.dataset(dataset_id).iterate_items())

print(items[0])
```

For a ready-to-run version with `.env` support, use [`run_markets.py`](./run_markets.py).

