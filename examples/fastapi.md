# FastAPI Example

Run this project as a small local REST API.

## Start the API

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open the API docs:

```text
http://127.0.0.1:8000/docs
```

## Call with an Authorization header

```bash
curl "http://127.0.0.1:8000/markets?exchange=all_exchanges&page=1" \
  -H "Authorization: Bearer apify_api_your_token_here"
```

Multiple exchanges:

```bash
curl "http://127.0.0.1:8000/markets?exchange=Binance&exchange=Bybit&page=1" \
  -H "Authorization: Bearer apify_api_your_token_here"
```

## Call with a local .env file

```bash
cp .env.example .env
```

Add your token:

```env
APIFY_TOKEN=apify_api_your_real_token_here
```

Start the API:

```bash
uvicorn app.main:app --reload
```

Then call it without sending the token in every request:

```bash
curl "http://127.0.0.1:8000/markets?exchange=Kraken&page=1"
```

## POST body

```bash
curl -X POST "http://127.0.0.1:8000/markets" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer apify_api_your_token_here" \
  -d '{"exchange":["Binance","Bybit"],"page":1}'
```

