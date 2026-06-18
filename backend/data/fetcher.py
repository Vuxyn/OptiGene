import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
import numpy as np
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Representative LQ45 tickers that are stable and have a listing history > 3 years (IPO before 2022)
LQ45_TICKERS = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "TLKM.JK", "ASII.JK",
    "UNVR.JK", "ADRO.JK", "PGAS.JK", "PTBA.JK", "INDF.JK",
    "ICBP.JK", "KLBF.JK", "CPIN.JK", "JSMR.JK", "BRPT.JK",
    "AKRA.JK", "EXCL.JK", "INCO.JK", "TPIA.JK", "SMGR.JK",
    "ANJT.JK", "ADHI.JK", "PWON.JK", "CTRA.JK", "MEDC.JK"
]

DEFAULT_BI_RATE = 0.0625  # Fallback 6.25%
DEFAULT_SBN_RATE = 0.0675 # Fallback 6.75%

def fetch_bi_rate() -> float:
    """
    Scrapes the latest BI Rate (Central Bank interest rate) from Bank Indonesia or Trading Economics.
    Uses default fallback rate if scraping fails.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Approach 1: Scraping Bank Indonesia official site
    try:
        url = "https://www.bi.go.id/id/default.aspx"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Look for the BI-Rate text on the homepage
            # Usually placed inside a specific widget / textbox
            elements = soup.find_all(text=True)
            for element in elements:
                if "BI-Rate" in element:
                    # Try to locate the percentage figure nearby
                    parent = element.parent
                    siblings = list(parent.parent.stripped_strings)
                    for sib in siblings:
                        if "%" in sib:
                            clean_val = sib.replace("%", "").replace(",", ".").strip()
                            rate = float(clean_val) / 100.0
                            logger.info(f"BI Rate successfully fetched from Bank Indonesia: {rate*100:.2f}%")
                            return rate
    except Exception as e:
        logger.warning(f"Failed to scrape BI Rate from Bank Indonesia: {e}")

    # Approach 2: Scraping Trading Economics (Indonesia Interest Rate)
    try:
        url = "https://tradingeconomics.com/indonesia/interest-rate"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Main indicator value is typically in a div with the class "value"
            val_div = soup.find("div", {"class": "value"})
            if val_div:
                rate = float(val_div.text.strip()) / 100.0
                logger.info(f"BI Rate successfully fetched from Trading Economics: {rate*100:.2f}%")
                return rate
            
            # Alternative: Search historical data table
            table = soup.find("table", {"id": "historical-data-table"})
            if table:
                first_row = table.find("tbody").find("tr")
                cells = first_row.find_all("td")
                rate = float(cells[1].text.strip()) / 100.0
                logger.info(f"BI Rate successfully fetched from Trading Economics Table: {rate*100:.2f}%")
                return rate
    except Exception as e:
        logger.warning(f"Failed to scrape BI Rate from Trading Economics: {e}")
        
    logger.info(f"Using fallback BI Rate: {DEFAULT_BI_RATE*100:.2f}%")
    return DEFAULT_BI_RATE

def fetch_sbn_rate() -> float:
    """
    Scrapes the latest 10-Year Government Bond Yield (SBN) from Trading Economics or CNBC Indonesia.
    Uses default fallback rate if scraping fails.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Approach 1: Scraping Trading Economics (Indonesia 10Y Government Bond Yield)
    try:
        url = "https://tradingeconomics.com/indonesia/government-bond-yield"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            val_div = soup.find("div", {"class": "value"})
            if val_div:
                rate = float(val_div.text.strip()) / 100.0
                logger.info(f"SBN 10Y Yield successfully fetched from Trading Economics: {rate*100:.2f}%")
                return rate
    except Exception as e:
        logger.warning(f"Failed to scrape SBN Yield from Trading Economics: {e}")
        
    # Approach 2: Scraping CNBC Indonesia Bond Market Page
    try:
        url = "https://www.cnbcindonesia.com/market/indeks-sbn"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Find table rows containing "10 Tahun" or similar
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

    logger.info(f"Using fallback SBN Yield: {DEFAULT_SBN_RATE*100:.2f}%")
    return DEFAULT_SBN_RATE

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
