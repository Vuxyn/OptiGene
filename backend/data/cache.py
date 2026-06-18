import os
import pandas as pd
import json
import logging

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache_store")

def _ensure_cache_dir():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def save_prices_cache(df_prices: pd.DataFrame, filename: str = "prices_cache.csv"):
    """
    Saves the asset prices DataFrame to a CSV cache file.
    """
    try:
        _ensure_cache_dir()
        path = os.path.join(CACHE_DIR, filename)
        df_prices.to_csv(path, index=True)
        logger.info(f"Asset prices successfully cached to: {path}")
    except Exception as e:
        logger.error(f"Failed to save asset price cache: {e}")

def load_prices_cache(filename: str = "prices_cache.csv") -> pd.DataFrame:
    """
    Loads the asset prices DataFrame from the CSV cache if it exists.
    """
    path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            logger.info(f"Successfully loaded asset prices from cache: {path}")
            return df
        except Exception as e:
            logger.error(f"Failed to read asset price cache: {e}")
    return pd.DataFrame()

def save_rates_cache(rates: dict, filename: str = "rates_cache.json"):
    """
    Saves rates (BI rate, SBN rate) to a JSON cache file.
    """
    try:
        _ensure_cache_dir()
        path = os.path.join(CACHE_DIR, filename)
        with open(path, "w") as f:
            json.dump(rates, f, indent=4)
        logger.info(f"Interest rates successfully cached to: {path}")
    except Exception as e:
        logger.error(f"Failed to save interest rates cache: {e}")

def load_rates_cache(filename: str = "rates_cache.json") -> dict:
    """
    Loads rates from the JSON cache if it exists.
    """
    path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                rates = json.load(f)
            logger.info(f"Successfully loaded interest rates from cache: {path}")
            return rates
        except Exception as e:
            logger.error(f"Failed to read interest rates cache: {e}")
    return {}
