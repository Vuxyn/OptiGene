import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def validate_assets(df_prices: pd.DataFrame, min_coverage: float = 0.95) -> tuple[pd.DataFrame, list[str]]:
    """
    Memvalidasi data historis harga aset berdasarkan kriteria:
    1. Masa listing minimal 3 tahun (harus aktif sejak awal periode 2022-01-01 hingga 2024-12-31).
    2. Coverage data penutupan harian >= 95% (persentase data non-NaN).
    
    Returns:
        df_cleaned: DataFrame harga aset yang lolos kualifikasi dengan NaN yang sudah di-interpolate/ffill.
        valid_tickers: List ticker yang lolos kualifikasi.
    """
    if df_prices.empty:
        logger.error("DataFrame input kosong, tidak ada data untuk divalidasi.")
        return pd.DataFrame(), []

    total_rows = len(df_prices)
    valid_tickers = []
    rejected_reasons = {}

    for col in df_prices.columns:
        series = df_prices[col]
        # 1. Hitung coverage data
        valid_count = series.notna().sum()
        coverage = valid_count / total_rows
        
        # 2. Cek apakah sudah terdaftar di awal periode (listing > 3 tahun dari akhir 2024)
        # Indeks pertama harus tidak NaN, atau setidaknya di awal-awal (misal 5% baris pertama)
        first_valid_idx = series.first_valid_index()
        is_listed_long_enough = False
        if first_valid_idx is not None:
            first_valid_pos = df_prices.index.get_loc(first_valid_idx)
            # Harus terdaftar di 5% baris pertama dari rentang waktu
            if first_valid_pos <= int(total_rows * 0.05):
                is_listed_long_enough = True

        # Evaluasi kelayakan
        if coverage >= min_coverage and is_listed_long_enough:
            valid_tickers.append(col)
        else:
            reason = []
            if coverage < min_coverage:
                reason.append(f"coverage rendah ({coverage*100:.1f}%)")
            if not is_listed_long_enough:
                reason.append("listing kurang dari 3 tahun (baru IPO)")
            rejected_reasons[col] = " dan ".join(reason)

    if rejected_reasons:
        for ticker, reason in rejected_reasons.items():
            logger.warning(f"Ticker {ticker} DI-REJECT karena: {reason}")
            
    logger.info(f"Hasil validasi: {len(valid_tickers)} / {len(df_prices.columns)} ticker lolos kualifikasi.")
    
    if not valid_tickers:
        logger.error("Tidak ada ticker yang memenuhi syarat validasi!")
        return pd.DataFrame(), []

    # Filter DataFrame hanya untuk kolom yang lolos
    df_filtered = df_prices[valid_tickers].copy()
    
    # Isi missing values (jika ada celah libur kecil) dengan forward fill kemudian backward fill
    df_cleaned = df_filtered.ffill().bfill()
    
    return df_cleaned, valid_tickers
