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
    Menyimpan DataFrame harga aset ke file cache CSV.
    """
    try:
        _ensure_cache_dir()
        path = os.path.join(CACHE_DIR, filename)
        df_prices.to_csv(path, index=True)
        logger.info(f"Harga aset berhasil disimpan ke cache: {path}")
    except Exception as e:
        logger.error(f"Gagal menyimpan cache harga: {e}")

def load_prices_cache(filename: str = "prices_cache.csv") -> pd.DataFrame:
    """
    Memuat DataFrame harga aset dari cache CSV jika ada.
    """
    path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            logger.info(f"Berhasil memuat harga aset dari cache: {path}")
            return df
        except Exception as e:
            logger.error(f"Gagal membaca cache harga: {e}")
    return pd.DataFrame()

def save_rates_cache(rates: dict, filename: str = "rates_cache.json"):
    """
    Menyimpan rates (BI rate, SBN rate) ke cache JSON.
    """
    try:
        _ensure_cache_dir()
        path = os.path.join(CACHE_DIR, filename)
        with open(path, "w") as f:
            json.dump(rates, f, indent=4)
        logger.info(f"Suku bunga berhasil disimpan ke cache: {path}")
    except Exception as e:
        logger.error(f"Gagal menyimpan cache suku bunga: {e}")

def load_rates_cache(filename: str = "rates_cache.json") -> dict:
    """
    Memuat rates dari cache JSON jika ada.
    """
    path = os.path.join(CACHE_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                rates = json.load(f)
            logger.info(f"Berhasil memuat suku bunga dari cache: {path}")
            return rates
        except Exception as e:
            logger.error(f"Gagal membaca cache suku bunga: {e}")
    return {}
