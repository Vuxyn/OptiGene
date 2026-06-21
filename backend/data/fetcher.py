import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
import numpy as np
import time
import logging
import os
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

LQ45_TICKERS = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "ASII.JK",
    "UNVR.JK", "ADRO.JK", "PGAS.JK", "PTBA.JK", "INDF.JK",
    "ICBP.JK", "KLBF.JK", "CPIN.JK", "JSMR.JK", "BRPT.JK",
    "AKRA.JK", "EXCL.JK", "INCO.JK", "TPIA.JK", "SMGR.JK",
    "ANJT.JK", "ADHI.JK", "PWON.JK", "CTRA.JK", "MEDC.JK"
]

DEFAULT_BI_RATE = 0.0625  # Fallback 6.25%
DEFAULT_SBN_RATE = 0.0675 # Fallback 6.75%

FALLBACK_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fallback_rates.json")

# Initialize fallback_rates.json with defaults if not present
try:
    if not os.path.exists(FALLBACK_CONFIG_PATH):
        config = {
            "bi_rate": DEFAULT_BI_RATE,
            "sbn_rate": DEFAULT_SBN_RATE
        }
        with open(FALLBACK_CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
        logger.info(f"Initialized default fallback rates config at: {FALLBACK_CONFIG_PATH}")
except Exception as e:
    logger.error(f"Failed to initialize fallback rates config: {e}")

def get_fallback_rate(rate_key: str, default_val: float) -> float:
    """
    Loads a fallback rate from the local config json file.
    """
    try:
        if os.path.exists(FALLBACK_CONFIG_PATH):
            with open(FALLBACK_CONFIG_PATH, "r") as f:
                config = json.load(f)
                if rate_key in config:
                    return float(config[rate_key])
    except Exception as e:
        logger.error(f"Failed to read fallback rates config: {e}")
    return default_val

def fetch_bi_rate() -> float:

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Scraping Trading Economics (Indonesia Interest Rate)
    try:
        url = "https://tradingeconomics.com/indonesia/interest-rate"
        response = requests.get(url, headers=headers, timeout=2.5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = [c.get_text().strip() for c in row.find_all(["td", "th"])]
                    if cells and cells[0] == "Interest Rate":
                        try:
                            rate = float(cells[1]) / 100.0
                            if 0.01 <= rate <= 0.15:
                                logger.info(f"BI Rate successfully fetched from Trading Economics table: {rate*100:.2f}%")
                                return rate
                        except (ValueError, IndexError):
                            pass
                            
            val_div = soup.find("div", {"class": "value"})
            if val_div:
                rate = float(val_div.text.strip()) / 100.0
                if 0.01 <= rate <= 0.15:
                    logger.info(f"BI Rate successfully fetched from Trading Economics div: {rate*100:.2f}%")
                    return rate
    except Exception as e:
        logger.warning(f"Failed to scrape BI Rate from Trading Economics: {e}")

    # Scraping Bank Indonesia official site
    try:
        url = "https://www.bi.go.id/id/default.aspx"
        response = requests.get(url, headers=headers, timeout=2.0)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            elements = soup.find_all(text=True)
            for element in elements:
                if "BI-Rate" in element:
                    parent = element.parent
                    siblings = list(parent.parent.stripped_strings)
                    for sib in siblings:
                        import re
                        match = re.search(r'(\d+(?:[\.,]\d+)?)', sib)
                        if match:
                            clean_val = match.group(1).replace(",", ".")
                            try:
                                rate = float(clean_val) / 100.0
                                if 0.01 <= rate <= 0.15:
                                    logger.info(f"BI Rate successfully fetched from Bank Indonesia: {rate*100:.2f}%")
                                    return rate
                            except ValueError:
                                continue
    except Exception as e:
        logger.warning(f"Failed to scrape BI Rate from Bank Indonesia: {e}")

    fallback_rate = get_fallback_rate("bi_rate", DEFAULT_BI_RATE)
    logger.info(f"Using fallback BI Rate: {fallback_rate*100:.2f}%")
    return fallback_rate

def fetch_sbn_rate() -> float:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Scraping Trading Economics (Indonesia 10Y Government Bond Yield)
    try:
        url = "https://tradingeconomics.com/indonesia/government-bond-yield"
        response = requests.get(url, headers=headers, timeout=2.5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = [c.get_text().strip() for c in row.find_all(["td", "th"])]
                    if cells and cells[0] == "Indonesia 10Y":
                        try:
                            rate = float(cells[1]) / 100.0
                            if 0.01 <= rate <= 0.20:
                                logger.info(f"SBN 10Y Yield successfully fetched from Trading Economics table: {rate*100:.2f}%")
                                return rate
                        except (ValueError, IndexError):
                            pass
                            
            val_div = soup.find("div", {"class": "value"})
            if val_div:
                rate = float(val_div.text.strip()) / 100.0
                if 0.01 <= rate <= 0.20:
                    logger.info(f"SBN 10Y Yield successfully fetched from Trading Economics div: {rate*100:.2f}%")
                    return rate
    except Exception as e:
        logger.warning(f"Failed to scrape SBN Yield from Trading Economics: {e}")
        
    # Scraping CNBC Indonesia Bond Market Page
    try:
        url = "https://www.cnbcindonesia.com/market/indeks-sbn"
        response = requests.get(url, headers=headers, timeout=2.0)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.find_all("tr")
            for row in rows:
                text = row.get_text()
                if "10 Tahun" in text or "10 Y" in text:
                    cells = row.find_all("td")
                    for cell in cells:
                        val = cell.get_text().strip().replace(",", ".")
                        if "%" in val:
                            rate = float(val.replace("%", "").strip()) / 100.0
                            logger.info(f"SBN 10Y Yield successfully fetched from CNBC Indonesia: {rate*100:.2f}%")
                            return rate
    except Exception as e:
        logger.warning(f"Failed to scrape SBN Yield from CNBC Indonesia: {e}")

    fallback_rate = get_fallback_rate("sbn_rate", DEFAULT_SBN_RATE)
    logger.info(f"Using fallback SBN Yield: {fallback_rate*100:.2f}%")
    return fallback_rate

def fetch_asset_prices(tickers: list, start_date: str = "2022-01-01", end_date: str = "2024-12-31") -> pd.DataFrame:
    """
    Fetches daily closing prices (Adjusted Close) for all tickers in parallel using yfinance.
    """
    logger.info(f"Downloading stock data from yfinance for {len(tickers)} tickers from {start_date} to {end_date}...")
    try:
        data = yf.download(tickers, start=start_date, end=end_date, progress=False)
        if "Adj Close" in data:
            df = data["Adj Close"]
        elif "Close" in data:
            df = data["Close"]
        else:
            df = data
            
        # If yfinance returns a Series (single ticker), convert to DataFrame
        if isinstance(df, pd.Series):
            df = df.to_frame(tickers[0])
            
        return df
    except Exception as e:
        logger.error(f"Failed to download data from yfinance: {e}")
        return pd.DataFrame()

def fetch_gold_prices(start_date: str = "2022-01-01", end_date: str = "2024-12-31") -> pd.Series:
    """
    Downloads gold price history using ticker ANTM.JK (with GC=F as global fallback).
    """
    ticker = "ANTM.JK"
    logger.info(f"Downloading gold prices ({ticker}) from yfinance...")
    try:
        df = fetch_asset_prices([ticker], start_date, end_date)
        if not df.empty and ticker in df:
            return df[ticker]
    except Exception as e:
        logger.warning(f"Failed to download {ticker} for gold: {e}")
        
    # Fallback to GC=F (Global Gold Futures)
    logger.info("Attempting fallback to global gold ticker GC=F...")
    try:
        df = fetch_asset_prices(["GC=F"], start_date, end_date)
        if not df.empty and "GC=F" in df:
            return df["GC=F"]
    except Exception as e:
        logger.error(f"Failed to download fallback gold GC=F: {e}")
        
    return pd.Series()
