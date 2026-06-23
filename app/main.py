from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import Any

from apify_client import ApifyClient
from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"
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


class CoinMarketsRequest(BaseModel):
    exchange: list[str] = Field(default_factory=lambda: ["all_exchanges"])
    page: int = Field(default=1, ge=0)


@asynccontextmanager
async def lifespan(_: FastAPI):
    load_env_file(ENV_FILE)
    yield


app = FastAPI(
    title="CoinGlass Coin Markets API",
    description="A tiny REST API wrapper around the Apify CoinGlass Coin Markets Actor.",
    version="1.0.0",
    lifespan=lifespan,
)


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


def is_real_token(token: str | None) -> bool:
    return bool(token and token.strip() and not token.strip().startswith("apify_api_your_"))


def get_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        return None

    return token.strip()


def get_apify_token(authorization: str | None = Header(default=None)) -> str:
    env_token = os.getenv("APIFY_TOKEN", "").strip()
    if is_real_token(env_token):
        return env_token

    header_token = get_bearer_token(authorization)
    if is_real_token(header_token):
        return header_token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Set APIFY_TOKEN in .env or send Authorization: Bearer <APIFY_TOKEN>.",
    )


def split_exchange_values(values: list[str] | None) -> list[str]:
    if not values:
        return ["all_exchanges"]

    exchanges: list[str] = []
    for value in values:
        exchanges.extend(item.strip() for item in str(value).split(",") if item.strip())

    unique_exchanges = list(dict.fromkeys(exchanges)) or ["all_exchanges"]
    if len(unique_exchanges) > 1 and "all_exchanges" in unique_exchanges:
        unique_exchanges = [exchange for exchange in unique_exchanges if exchange != "all_exchanges"]

    unsupported = [exchange for exchange in unique_exchanges if exchange not in SUPPORTED_EXCHANGES]
    if unsupported:
        supported = ", ".join(sorted(SUPPORTED_EXCHANGES))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported exchange: {', '.join(unsupported)}. Supported values: {supported}.",
        )

    return unique_exchanges


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


def get_run_error_detail(
    client: ApifyClient,
    run: object,
    run_input: dict[str, Any],
) -> dict[str, Any]:
    dataset_id = get_run_value(run, "defaultDatasetId", "default_dataset_id")
    dataset_items: list[dict[str, Any]] = []

    if dataset_id:
        try:
            dataset_items = list(client.dataset(str(dataset_id)).iterate_items())
        except Exception:
            dataset_items = []

    detail: dict[str, Any] = {
        "message": "Actor run did not succeed.",
        "actor": ACTOR_ID,
        "runId": get_run_value(run, "id"),
        "status": get_run_value(run, "status"),
        "statusMessage": get_run_value(run, "statusMessage", "status_message"),
        "exitCode": get_run_value(run, "exitCode", "exit_code"),
        "datasetId": dataset_id,
        "input": run_input,
    }

    if dataset_items:
        detail["datasetItems"] = dataset_items

    return detail


def fetch_markets(token: str, request: CoinMarketsRequest) -> dict[str, Any]:
    exchanges = split_exchange_values(request.exchange)
    page = request.page if request.page > 0 else 1
    run_input = {
        "exchange": exchanges,
        "page": page,
    }

    client = ApifyClient(token)
    try:
        run = client.actor(ACTOR_ID).call(run_input=run_input)

        run_status = get_run_value(run, "status")
        if run_status and run_status != "SUCCEEDED":
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=get_run_error_detail(client, run, run_input),
            )

        dataset_id = get_run_value(run, "defaultDatasetId", "default_dataset_id")
        if not dataset_id:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Actor run did not return a default dataset id.",
            )

        items = list(client.dataset(str(dataset_id)).iterate_items())
        if not items:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Actor finished, but the default dataset is empty.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Apify request failed. Check your token, actor access, and input values.",
        ) from exc

    return {
        "success": True,
        "actor": ACTOR_ID,
        "runId": get_run_value(run, "id"),
        "datasetId": dataset_id,
        "input": run_input,
        "data": items[0] if len(items) == 1 else items,
    }


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "CoinGlass Coin Markets API",
        "endpoints": {
            "health": "/health",
            "markets": "/markets?exchange=all_exchanges&page=1",
            "docs": "/docs",
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/markets")
async def get_markets(
    exchange: list[str] | None = Query(default=None),
    page: int = Query(default=1, ge=0),
    token: str = Depends(get_apify_token),
) -> dict[str, Any]:
    request = CoinMarketsRequest(exchange=split_exchange_values(exchange), page=page)
    return await run_in_threadpool(fetch_markets, token, request)


@app.post("/markets")
async def post_markets(
    request: CoinMarketsRequest,
    token: str = Depends(get_apify_token),
) -> dict[str, Any]:
    return await run_in_threadpool(fetch_markets, token, request)
