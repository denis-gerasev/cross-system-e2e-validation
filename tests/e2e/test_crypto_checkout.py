"""Hybrid E2E/Integration test: cross-references a live Binance BTC/USD quote
against a cart subtotal computed in the React shopping cart's UI.

See README.md ("Why This Hybrid Approach Was Chosen") for the rationale.
This adds no crypto awareness to the app itself - it has none. The test
layer alone combines two independently-exercised systems:

 1. the real DOM, to read the USD subtotal the UI actually computed (and
    check it against the app's own product catalogue), and
 2. the live Binance feed, converted to a BTC amount by
    `BinanceClient.usd_to_btc`, which refuses corrupted quotes (see
    `test_market_data.py` for the API-only version of that check).
"""
from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path

import pytest

from src.api_clients.binance_client import SATOSHI, BinanceClient, CorruptedPriceDataError
from src.page_objects.page_objects import ShoppingCartPage

# $10.90, 9 instalments - a fixed catalog entry so the expected subtotal is
# deterministic across runs.
PRODUCT_TITLE = "Cropped Stay Groovy off white"

# The app's own seed catalogue: an independent source of truth for what the
# UI should charge. (The deployed app reads the same data from Firebase.)
_CATALOG = Path(__file__).resolve().parents[2] / "react-shopping-cart/src/static/json/products.json"


def _catalog_price(title: str) -> Decimal:
    products = json.loads(_CATALOG.read_text(encoding="utf-8"))["data"]["products"]
    return Decimal(str(next(p["price"] for p in products if p["title"] == title)))


def test_crypto_checkout_total_matches_live_rate(store_page, live_book_ticker):
    # 1. Fail fast on a bad feed, before driving the browser.
    BinanceClient.validate(live_book_ticker)

    # 2. Drive the real UI and read back the USD subtotal it computed.
    cart = ShoppingCartPage(store_page)
    cart.add_to_cart(PRODUCT_TITLE)
    usd_subtotal = cart.subtotal()

    # 3. UI side: the subtotal must match the catalogue price, not just be "some number".
    assert usd_subtotal == _catalog_price(PRODUCT_TITLE)

    # 4. Feed side: convert at the live ask price (what buying BTC costs).
    btc_total = BinanceClient.usd_to_btc(usd_subtotal, live_book_ticker)
    assert btc_total > 0

    # 5. Formatting: a plain 8-decimal amount. str(Decimal) can switch to
    #    scientific notation for small values ('1E-7'), which would break an invoice.
    assert re.fullmatch(r"\d+\.\d{8}", format(btc_total, "f"))

    # 6. Rounding to one satoshi may move the amount by at most half a
    #    satoshi, i.e. ask * SATOSHI / 2 when converted back to USD.
    ask = live_book_ticker.ask_price
    assert abs(btc_total * ask - usd_subtotal) <= ask * SATOSHI / 2

    # 7. The UI's own checkout dialog must agree with what we read from the DOM.
    confirmation = cart.checkout()
    assert confirmation == f"Checkout - Subtotal: $ {usd_subtotal:.2f}"


def test_corrupted_feed_blocks_checkout_conversion(store_page, corrupted_book_ticker):
    """The conversion must refuse a corrupted feed rather than silently
    producing a nonsense BTC total from a perfectly good UI subtotal."""
    cart = ShoppingCartPage(store_page)
    cart.add_to_cart(PRODUCT_TITLE)
    usd_subtotal = cart.subtotal()
    assert usd_subtotal == _catalog_price(PRODUCT_TITLE)  # the UI side is healthy...

    with pytest.raises(CorruptedPriceDataError):
        # ...but the feed isn't, so no BTC total may be derived from it.
        BinanceClient.usd_to_btc(usd_subtotal, corrupted_book_ticker)
