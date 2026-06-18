import numpy as np
import pandas as pd
import logging
import os
from backend.data.fetcher import fetch_bi_rate, fetch_sbn_rate, fetch_asset_prices, fetch_gold_prices, LQ45_TICKERS
from backend.data.validator import validate_assets
from backend.data.cache import load_prices_cache, save_prices_cache, load_rates_cache, save_rates_cache
from backend.pyspark.session import get_spark_session
from backend.pyspark.context import compute_asset_stats_sql
from backend.ga.optimizer import GeneticOptimizer
from backend.formatter import format_layman_results

logger = logging.getLogger(__name__)

def optimize_portfolio_flow(
    capital: float, 
    risk_profile: str, 
    duration_years: int = 3, 
    mode: str = "numpy_vectorized"
) -> dict:
    """
    Mengkoordinasikan seluruh alur kerja aplikasi OptiGene dari fetching data,
    kalkulasi statistik, eksekusi GA, hingga pemformatan ramah pemula.
    """
    logger.info("Memulai alur optimasi portofolio OptiGene...")
    
    # 1. Ambil atau Muat Suku Bunga (BI Rate & SBN)
    rates = load_rates_cache()
    if not rates:
        bi_rate = fetch_bi_rate()
        sbn_rate = fetch_sbn_rate()
        rates = {"bi_rate": bi_rate, "sbn_rate": sbn_rate}
        save_rates_cache(rates)
    else:
        bi_rate = rates["bi_rate"]
        sbn_rate = rates["sbn_rate"]
        
    # 2. Ambil atau Muat Harga Historis Saham & Emas (2022 - 2024)
    df_prices = load_prices_cache()
    if df_prices.empty:
        # Fetch Emas (ANTM.JK)
        s_gold = fetch_gold_prices()
        # Fetch Saham LQ45
        df_stocks = fetch_asset_prices(LQ45_TICKERS)
        
        # Gabungkan
        if not s_gold.empty:
            df_stocks["EMAS"] = s_gold
            
        df_prices = df_stocks
        
        # Validasi Aset (listing > 3 tahun, data coverage >= 95%)
        df_prices, valid_tickers = validate_assets(df_prices, min_coverage=0.95)
        
        # Simpan ke cache jika sukses
        if not df_prices.empty:
            save_prices_cache(df_prices)
    else:
        valid_tickers = df_prices.columns.tolist()

    if df_prices.empty:
        raise RuntimeError("Gagal memuat data historis harga aset yang valid.")

    # 3. Hitung Return Harian untuk Aset Dinamis (Saham & Emas)
    df_returns_dynamic = df_prices.pct_change().dropna()
    
    # 4. Integrasikan Aset Fixed Income (Deposito & SBN)
    # Deposito memiliki rate harian konstan = bi_rate / 252
    # SBN memiliki rate harian konstan = sbn_rate / 252
    T = len(df_returns_dynamic)
    
    deposito_daily_ret = bi_rate / 252.0
    sbn_daily_ret = sbn_rate / 252.0
    
    # Buat DataFrame return lengkap (Deposito, SBN, Emas, Saham)
    df_returns = pd.DataFrame(index=df_returns_dynamic.index)
    df_returns["DEPOSITO"] = np.full(T, deposito_daily_ret)
    df_returns["SBN ORI"] = np.full(T, sbn_daily_ret)
    
    for col in df_returns_dynamic.columns:
        df_returns[col] = df_returns_dynamic[col]
        
    # Nama semua aset berurutan
    asset_names = df_returns.columns.tolist()
    N = len(asset_names)
    
    # 5. Hitung Statistik Aset (Expected Return & Covariance)
    # Gunakan Spark SQL untuk menghitung statistik historis jika Spark aktif
    # (Opsional/Bisa CPU fallback untuk kecepatan inisialisasi)
    spark = None
    if "pyspark" in mode.lower():
        try:
            spark = get_spark_session()
            df_stats_sql = compute_asset_stats_sql(spark, df_returns)
            
            # Petakan hasil SQL ke array mu
            mu_dict = dict(zip(df_stats_sql["Asset"], df_stats_sql["expected_return"]))
            mu = np.array([mu_dict.get(asset, 0.0) for asset in asset_names])
        except Exception as e:
            logger.error(f"Gagal hitung statistik via Spark SQL: {e}. Menggunakan NumPy CPU.")
            # Fallback expected return CPU
            mu = df_returns.mean().values * 252.0
    else:
        # NumPy CPU expected return
        mu = df_returns.mean().values * 252.0
        
    # Untuk Deposito dan SBN, paksa expected return-nya persis ke suku bunga tahunan
    mu[0] = bi_rate
    mu[1] = sbn_rate
    
    # Hitung matriks kovarians (disetahunkan)
    # Covariance Deposito dan SBN dengan aset lain akan bernilai 0 karena konstan
    # Kita hitung via NumPy CPU (cepat) atau GPU jika CuPy aktif dan mode="cuda"
    if mode == "cuda":
        from backend.cuda.kernels import gpu_compute_covariance, CUDA_AVAILABLE
        if CUDA_AVAILABLE:
            try:
                means = df_returns.mean().values
                Sigma = gpu_compute_covariance(df_returns.values, means)
            except Exception as e:
                logger.error(f"Gagal hitung kovarians di GPU: {e}. Melakukan fallback ke CPU.")
                Sigma = np.cov(df_returns.values, rowvar=False) * 252.0
        else:
            Sigma = np.cov(df_returns.values, rowvar=False) * 252.0
    else:
        Sigma = np.cov(df_returns.values, rowvar=False) * 252.0
        
    # Bersihkan matrix cov agar tidak ada nilai NaN/Inf
    Sigma = np.nan_to_num(Sigma, nan=0.0, posinf=0.0, neginf=0.0)

    # 6. Hitung Pergerakan Harga Relatif Historis (P_rel) untuk Max Drawdown
    # P_rel = T x N
    P_rel = np.zeros((T + 1, N))
    
    # Hari ke-0 bernilai 1.0 (baseline)
    P_rel[0, :] = 1.0
    
    # Untuk Deposito & SBN: tumbuh konstan (1 + daily_return)^t
    # Untuk Saham & Emas: harga relatif terhadap harga awal
    for t in range(1, T + 1):
        P_rel[t, 0] = (1.0 + deposito_daily_ret) ** t
        P_rel[t, 1] = (1.0 + sbn_daily_ret) ** t
        
    # Dinamis (Saham & Emas)
    # df_prices_matched mencakup harga harian
    # Kita cari harga penutupan awal
    for col_idx, col_name in enumerate(asset_names[2:], start=2):
        initial_price = df_prices[col_name].iloc[0]
        # Pastikan tidak pembagian nol
        if initial_price > 0:
            prices_rel = df_prices[col_name].values / initial_price
            # Cocokkan panjang dengan T + 1
            P_rel[:, col_idx] = prices_rel[:T+1]
        else:
            P_rel[:, col_idx] = 1.0

    # 7. Jalankan Genetic Algorithm Optimizer
    # Gunakan parameter default GA (1000 populasi, 500 generasi)
    optimizer = GeneticOptimizer(pop_size=1000, generations=500)
    
    # Pastikan Spark session diteruskan ke optimizer jika mode PySpark digunakan
    if "pyspark" in mode.lower() and spark is None:
        spark = get_spark_session()
        
    ga_results = optimizer.run(mu, Sigma, P_rel, risk_profile, mode=mode, spark=spark)
    
    # Tambahkan metadata nama aset untuk formatter
    ga_results["asset_names"] = asset_names
    
    # 8. Format Output ke Bahasa Awam
    layman_formatted = format_layman_results(ga_results, capital, duration_years)
    
    return layman_formatted
