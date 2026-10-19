import pytest

from src.api_clients.binance_client import BinanceClient, CorruptedPriceDataError


def test_corrupted_data(corrupted_book_ticker):
    """A deliberately inverted feed (bid > ask) must be rejected, not just
    re-checked with the same assertions the live feed uses - that would
    always fail, since the fixture is inverted on purpose."""
    with pytest.raises(CorruptedPriceDataError):
        BinanceClient.validate(corrupted_book_ticker)


def test_live_data(live_book_ticker):
    # Should not raise: a healthy live feed passes the same check that
    # rejects the corrupted fixture above.
    BinanceClient.validate(live_book_ticker)

    assert live_book_ticker.bid_price > 0
    assert live_book_ticker.ask_price > 0

    assert live_book_ticker.ask_price > live_book_ticker.bid_price

    print("Live data is validated")
