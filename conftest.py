import pytest
from src.api_clients.binance_client import BinanceClient, BookTicker
from src.config.env_config import Config
from decimal import Decimal

# 1. The Global Setup (Runs once per test run)
@pytest.fixture(scope="session", autouse=True)
def display_test_environment():
    """Prints the current target URLs to the terminal before tests start."""
    Config.print_startup_state()

# 2. The Browser Setup (Runs once per test)
@pytest.fixture
def store_page(page):
    """
    Automates the Playwright setup. 
    Grabs the correct URL from the Brain, navigates there, and hands the browser to the test.
    """
    # Ask the Brain for the URL (Local or Live)
    target_url = Config.get_ui_url()
    
    # Navigate the browser to the React app
    page.goto(target_url)
    
    # Hand the ready-to-use browser to the test
    yield page

@pytest.fixture(scope="session")
def binance_client():
    """The one client every Binance-touching fixture/test shares."""
    return BinanceClient()

@pytest.fixture
def live_book_ticker(binance_client):
    """A single live BTCUSDT quote, fetched once per test that needs it."""
    return binance_client.get_book_ticker("BTCUSDT")

@pytest.fixture
def live_price_data(live_book_ticker):
    """
    Provide live API data.

    Kept as a raw string dict (Binance's own JSON shape) for
    backward-compatibility with tests written against it directly;
    `live_book_ticker` is the typed equivalent and does the actual network
    call, so this fixture costs no extra request.
    """
    return {
        "bidPrice": str(live_book_ticker.bid_price),
        "askPrice": str(live_book_ticker.ask_price),
    }

@pytest.fixture
def corrupted_price_data():
    return {"bidPrice":100.0, "askPrice":90.0}

@pytest.fixture
def corrupted_book_ticker(corrupted_price_data):
    """`corrupted_price_data`, typed - deliberately inverted (bid > ask)."""
    return BookTicker(
        symbol="BTCUSDT",
        bid_price=Decimal(str(corrupted_price_data["bidPrice"])),
        ask_price=Decimal(str(corrupted_price_data["askPrice"])),
    )
