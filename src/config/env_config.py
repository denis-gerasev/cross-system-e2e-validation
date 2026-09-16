import os

class Config:
    """
    Master configuration class for the test framework.
    Reads system environment variables to determine where tests should point.
    """
    
    # 1. Determine the environment (Defaults to 'local' if nothing is specified)
    ENV = os.getenv("TEST_ENV", "local").lower()

    # 2. API Endpoints (These remain static regardless of UI environment)
    BINANCE_BASE_URL = "https://api.binance.com/api/v3"
    
    @classmethod
    def get_ui_url(cls):
        """Returns the correct frontend URL based on the environment."""
        if cls.ENV == "live":
            # The live production deployment of Jefferson's app
            return "https://jeffersonribeiro.github.io/react-shopping-cart/"
        elif cls.ENV == "local":
            # Your locally running instance of the app
            return "http://localhost:3000"
        else:
            raise ValueError(f"Unsupported environment: {cls.ENV}. Use 'local' or 'live'.")

    @classmethod
    def print_startup_state(cls):
        """Helper to print the current configuration when tests start."""
        print(f"\n--- TEST RUN STARTED ---")
        print(f"Environment: {cls.ENV.upper()}")
        print(f"Target UI:   {cls.get_ui_url()}")
        print(f"Target API:  {cls.BINANCE_BASE_URL}")
        print(f"------------------------\n")