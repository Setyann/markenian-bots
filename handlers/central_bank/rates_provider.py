import asyncio
import os
import time
from typing import Iterable

import aiohttp


DEFAULT_API_URL = "https://v6.exchangerate-api.com/v6"
DEFAULT_TIMEOUT = 6.0
DEFAULT_CACHE_TTL = 300

_CACHE: dict[str, float] | None = None
_CACHE_TS: float | None = None
_LOCK = asyncio.Lock()


class RatesProviderError(RuntimeError):
    def __init__(self, code: str, message: str | None = None):
        super().__init__(message or code)
        self.code = code


def _api_url() -> str:
    return os.getenv("EXCHANGE_RATE_API_URL") or DEFAULT_API_URL


def _api_key() -> str:
    return os.getenv("EXCHANGE_RATE_API_KEY") or ""


def _timeout() -> float:
    try:
        return float(os.getenv("USD_RATES_TIMEOUT") or DEFAULT_TIMEOUT)
    except ValueError:
        return DEFAULT_TIMEOUT


def _cache_ttl() -> int:
    try:
        return int(os.getenv("USD_RATES_CACHE_TTL") or DEFAULT_CACHE_TTL)
    except ValueError:
        return DEFAULT_CACHE_TTL


def _is_cache_fresh() -> bool:
    if _CACHE is None or _CACHE_TS is None:
        return False
    return (time.monotonic() - _CACHE_TS) < _cache_ttl()


def _subset(rates: dict[str, float], currencies: Iterable[str]) -> dict[str, float]:
    result: dict[str, float] = {}
    for code in currencies:
        rate = rates.get(code)
        if rate is None:
            continue
        result[code] = float(rate)
    return result


async def _fetch_rates() -> dict[str, float]:
    api_key = _api_key()
    if not api_key:
        raise RatesProviderError("missing_api_key")

    url = f"{_api_url().rstrip('/')}/{api_key}/latest/USD"
    timeout = aiohttp.ClientTimeout(total=_timeout())
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise RatesProviderError("http_error", f"status={resp.status}")
            data = await resp.json()

    if not isinstance(data, dict) or data.get("result") != "success":
        raise RatesProviderError("bad_response")
    rates = data.get("conversion_rates")
    if not isinstance(rates, dict):
        raise RatesProviderError("bad_response")

    cleaned: dict[str, float] = {}
    for code, value in rates.items():
        try:
            cleaned[str(code)] = float(value)
        except (TypeError, ValueError):
            continue
    if not cleaned:
        raise RatesProviderError("bad_response")
    return cleaned


async def get_usd_rates(currencies: Iterable[str]) -> dict[str, float]:
    global _CACHE, _CACHE_TS
    if _is_cache_fresh() and _CACHE is not None:
        return _subset(_CACHE, currencies)

    async with _LOCK:
        if _is_cache_fresh() and _CACHE is not None:
            return _subset(_CACHE, currencies)
        try:
            rates = await _fetch_rates()
            _CACHE = rates
            _CACHE_TS = time.monotonic()
        except RatesProviderError:
            if _CACHE is not None:
                return _subset(_CACHE, currencies)
            raise

    return _subset(_CACHE or {}, currencies)
