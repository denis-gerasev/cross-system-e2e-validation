import pytest
import requests
from src.config.env_config import Config
from unittest.mock import patch

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

@pytest.fixture
def live_price_data():
    r = requests.get('https://api.binance.com/api/v3/ticker/bookTicker?symbol=BTCUSDT')

    print (r.status_code)

    data = r.json()

    bidPrice = data['bidPrice']
    askPrice = data['askPrice']

    return bidPrice
    return askPrice

def corrupted_price_data():
    bidPrice = 100
    askPrice = 90

    return bidPrice
    return askPrice

    