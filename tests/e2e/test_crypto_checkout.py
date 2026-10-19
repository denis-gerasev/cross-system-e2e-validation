"""Hybrid E2E/Integration test: cross-references a live Binance BTC/USD quote
against a cart subtotal computed in the React shopping cart's UI.

See README.md ("Why This Hybrid Approach Was Chosen") for the rationale.
This adds no crypto awareness to the app itself - it has none. The test
layer alone combines two independently-exercised systems:

 1. the real DOM, to read the USD subtotal the UI actually computed, and
 2. the live Binance feed, to get a BTC/USD conversion rate - after first
    confirming that feed isn't corrupted (see `test_market_data.py` for the
    API-only version of that same check).
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from src.api_clients.binance_client import BinanceClient, CorruptedPriceDataError
from src.page_objects.page_objects import ShoppingCartPage

# $10.90, 9 instalments - a fixed catalog entry so the expected subtotal is
# deterministic across runs (see react-shopping-cart-e2e/test_data for the
# full catalog this app is seeded with).
PRODUCT_TITLE = "Cropped Stay Groovy off white"


def test_crypto_checkout_total_matches_live_rate(store_page, live_book_ticker):
    # 1. Confirm the live feed is usable before trusting it with real money math.
    BinanceClient.validate(live_book_ticker)

    # 2. Drive the real UI and read back the USD subtotal it computed.
    cart = ShoppingCartPage(store_page)
    cart.add_to_cart(PRODUCT_TITLE)
    usd_subtotal = cart.subtotal()
    assert usd_subtotal > 0

    # 3. Convert using the live ask price (the rate you'd pay to buy BTC).
    btc_equivalent = usd_subtotal / live_book_ticker.ask_price
    assert btc_equivalent > 0

    # 4. The conversion must be internally consistent both ways.
    assert abs(btc_equivalent * live_book_ticker.ask_price - usd_subtotal) < Decimal("0.01")

    # 5. The UI's own checkout dialog must agree with what we read from the DOM.
    confirmation = cart.checkout()
    assert confirmation == f"Checkout - Subtotal: $ {usd_subtotal:.2f}"


def test_corrupted_feed_blocks_checkout_conversion(store_page, corrupted_book_ticker):
    """The pipeline must refuse to convert a UI-computed subtotal using a
    corrupted feed, rather than silently producing a nonsense BTC total."""
    cart = ShoppingCartPage(store_page)
    cart.add_to_cart(PRODUCT_TITLE)
    usd_subtotal = cart.subtotal()
    assert usd_subtotal > 0  # the UI side of the pipeline is healthy...

    with pytest.raises(CorruptedPriceDataError):
        # ...but the feed isn't, so no BTC total may be derived from it.
        BinanceClient.validate(corrupted_book_ticker)
