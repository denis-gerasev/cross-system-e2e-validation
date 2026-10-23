"""Thin wrapper around the public Binance REST API.

This centralizes the one network call this project depends on (a raw
``requests.get`` used to live inline in ``conftest.py``) plus the defensive
validation every caller needs: a book-ticker quote is only usable if both
sides are positive and the ask is strictly above the bid. See README.md
("Defensive Testing & Domain Knowledge") for why that check exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

import requests

from src.config.env_config import Config

# Smallest BTC unit (one satoshi) - amounts are rounded to this many places.
SATOSHI = Decimal("0.00000001")


class CorruptedPriceDataError(ValueError):
    """Raised when a market data payload fails the sanity checks in `validate`."""


@dataclass(frozen=True)
class BookTicker:
    """A bid/ask quote for one symbol, as returned by Binance's bookTicker endpoint."""

    symbol: str
    bid_price: Decimal
    ask_price: Decimal

    @property
    def mid_price(self) -> Decimal:
        return (self.bid_price + self.ask_price) / 2


class BinanceClient:
    """Minimal client for the public endpoints this suite needs."""

    def __init__(self, base_url: str | None = None, timeout: float = 5.0) -> None:
        self.base_url = base_url or Config.BINANCE_BASE_URL
        self.timeout = timeout

    def get_book_ticker(self, symbol: str = "BTCUSDT") -> BookTicker:
        """Fetch the current best bid/ask for `symbol`.

        Raises ``requests.HTTPError`` on a non-2xx response. Does not validate
        the payload - call `validate` on the result before trusting it for
        any downstream calculation.
        """
        response = requests.get(
            f"{self.base_url}/ticker/bookTicker",
            params={"symbol": symbol},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return BookTicker(
            symbol=payload["symbol"],
            bid_price=Decimal(payload["bidPrice"]),
            ask_price=Decimal(payload["askPrice"]),
        )

    @staticmethod
    def validate(ticker: BookTicker) -> None:
        """Raise `CorruptedPriceDataError` if `ticker` is not safe to use.

        A feed is considered corrupted if either side is non-positive, or the
        ask is not strictly above the bid (a crossed or locked book is not a
        valid state for a live order book snapshot).
        """
        if ticker.bid_price <= 0 or ticker.ask_price <= 0:
            raise CorruptedPriceDataError(f"Non-positive price in {ticker!r}")
        if ticker.ask_price <= ticker.bid_price:
            raise CorruptedPriceDataError(
                f"Ask ({ticker.ask_price}) is not above bid ({ticker.bid_price}) in {ticker!r}"
            )

    @staticmethod
    def usd_to_btc(usd_amount: Decimal, ticker: BookTicker) -> Decimal:
        """Convert a USD amount to BTC at the ask price (what buying BTC costs).

        The quote is validated first, so a corrupted feed raises
        `CorruptedPriceDataError` instead of silently producing a number.
        The result is rounded to one satoshi (8 decimal places).
        """
        if ticker.symbol != "BTCUSDT":
            raise ValueError(f"Expected a BTCUSDT quote, got {ticker.symbol!r}")
        if usd_amount < 0:
            raise ValueError(f"USD amount cannot be negative: {usd_amount}")
        BinanceClient.validate(ticker)
        return (usd_amount / ticker.ask_price).quantize(SATOSHI, rounding=ROUND_HALF_UP)
