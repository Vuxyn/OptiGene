import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
import numpy as np
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# List ticker LQ45 representatif yang stabil dan memiliki masa listing > 3 tahun (IPO sebelum 2022)
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
    Scrape suku bunga BI Rate terbaru dari situs resmi Bank Indonesia atau tradingeconomics.
    Jika gagal, gunakan fallback suku bunga default.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Pendekatan 1: Scraping Bank Indonesia
    try:
        url = "https://www.bi.go.id/id/default.aspx"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Mencari teks BI-Rate di halaman utama
            # Biasanya diletakkan di dalam widget / text-box tertentu
            # Kita cari elemen yang mengandung teks "BI-Rate"
            elements = soup.find_all(text=True)
            for element in elements:
                if "BI-Rate" in element:
                    # Coba temukan angka persentase di sekitarnya
                    parent = element.parent
                    siblings = list(parent.parent.stripped_strings)
                    for sib in siblings:
                        if "%" in sib:
                            clean_val = sib.replace("%", "").replace(",", ".").strip()
                            rate = float(clean_val) / 100.0
                            logger.info(f"BI Rate berhasil didapatkan dari Bank Indonesia: {rate*100:.2f}%")
                            return rate
    except Exception as e:
        logger.warning(f"Gagal melakukan scraping BI Rate dari Bank Indonesia: {e}")

    # Pendekatan 2: Scraping Trading Economics (Indonesia Interest Rate)
    try:
        url = "https://tradingeconomics.com/indonesia/interest-rate"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Angka terakhir biasanya di dalam div dengan kelas khusus atau table
            # TradingEconomics memiliki tabel / div kelas "value" untuk indikator utama
            val_div = soup.find("div", {"class": "value"})
            if val_div:
                rate = float(val_div.text.strip()) / 100.0
                logger.info(f"BI Rate berhasil didapatkan dari Trading Economics: {rate*100:.2f}%")
                return rate
            
            # Alternatif: Cari dari tabel data historis di trading economics
            table = soup.find("table", {"id": "historical-data-table"})
            if table:
                first_row = table.find("tbody").find("tr")
                cells = first_row.find_all("td")
                rate = float(cells[1].text.strip()) / 100.0
                logger.info(f"BI Rate berhasil didapatkan dari Trading Economics Table: {rate*100:.2f}%")
                return rate
    except Exception as e:
        logger.warning(f"Gagal melakukan scraping BI Rate dari Trading Economics: {e}")
        
    logger.info(f"Menggunakan fallback BI Rate: {DEFAULT_BI_RATE*100:.2f}%")
    return DEFAULT_BI_RATE

def fetch_sbn_rate() -> float:
    """
    Scrape imbal hasil/kupon SBN terbaru (10-Year Government Bond Yield) dari CNBC Indonesia / Trading Economics.
    Jika gagal, gunakan fallback rate default.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Pendekatan 1: Scraping Trading Economics (10Y Government Bond Yield Indonesia)
    try:
        url = "https://tradingeconomics.com/indonesia/government-bond-yield"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            val_div = soup.find("div", {"class": "value"})
            if val_div:
                rate = float(val_div.text.strip()) / 100.0
                logger.info(f"SBN 10Y Yield berhasil didapatkan dari Trading Economics: {rate*100:.2f}%")
                return rate
    except Exception as e:
        logger.warning(f"Gagal melakukan scraping SBN Yield dari Trading Economics: {e}")
        
    # Pendekatan 2: Scraping CNBC Indonesia Bond Market Page
    try:
        url = "https://www.cnbcindonesia.com/market/indeks-sbn"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Temukan baris tabel yang mengandung tenor "10 Tahun" atau serupa
            rows = soup.find_all("tr")
            for row in rows:
                text = row.get_text()
                if "10 Tahun" in text or "10 Y" in text:
                    cells = row.find_all("td")
                    for cell in cells:
                        val = cell.get_text().strip().replace(",", ".")
                        if "%" in val:
                            rate = float(val.replace("%", "").strip()) / 100.0
                            logger.info(f"SBN 10Y Yield berhasil didapatkan dari CNBC Indonesia: {rate*100:.2f}%")
                            return rate
    except Exception as e:
        logger.warning(f"Gagal melakukan scraping SBN Yield dari CNBC Indonesia: {e}")

    logger.info(f"Menggunakan fallback SBN Yield: {DEFAULT_SBN_RATE*100:.2f}%")
    return DEFAULT_SBN_RATE

def fetch_asset_prices(tickers: list, start_date: str = "2022-01-01", end_date: str = "2024-12-31") -> pd.DataFrame:
    """
    Fetch data harga penutupan harian (Adjusted Close) untuk semua ticker dalam list secara bersamaan menggunakan yfinance.
    """
    logger.info(f"Mengunduh data saham dari yfinance untuk {len(tickers)} ticker dari {start_date} ke {end_date}...")
    try:
        # Mengunduh data Close price
        data = yf.download(tickers, start=start_date, end=end_date, progress=False)
        if "Adj Close" in data:
            df = data["Adj Close"]
        elif "Close" in data:
            df = data["Close"]
        else:
            df = data
            
        # Jika yfinance mengembalikan series (jika hanya 1 ticker), ubah menjadi DataFrame
        if isinstance(df, pd.Series):
            df = df.to_frame(tickers[0])
            
        return df
    except Exception as e:
        logger.error(f"Gagal mengunduh data dari yfinance: {e}")
        return pd.DataFrame()

def fetch_gold_prices(start_date: str = "2022-01-01", end_date: str = "2024-12-31") -> pd.Series:
    """
    Mengunduh data emas menggunakan ticker ANTM.JK (atau GC=F jika ANTM bermasalah).
    """
    ticker = "ANTM.JK"
    logger.info(f"Mengunduh data emas ({ticker}) dari yfinance...")
    try:
        df = fetch_asset_prices([ticker], start_date, end_date)
        if not df.empty and ticker in df:
            return df[ticker]
    except Exception as e:
        logger.warning(f"Gagal mengunduh ANTM.JK untuk emas: {e}")
        
    # Fallback ke GC=F (Emas global)
    logger.info("Mencoba fallback emas ke ticker global GC=F...")
    try:
        df = fetch_asset_prices(["GC=F"], start_date, end_date)
        if not df.empty and "GC=F" in df:
            return df["GC=F"]
    except Exception as e:
        logger.error(f"Gagal mengunduh fallback emas GC=F: {e}")
        
    return pd.Series()
