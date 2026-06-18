from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def compute_asset_stats_sql(spark: SparkSession, df_returns: pd.DataFrame) -> pd.DataFrame:
    """
    Menggunakan SparkSession SQL Query untuk menghitung rata-rata return tahunan
    dan volatilitas/varian tahunan per aset dari data return harian.
    """
    logger.info("Menghitung statistik aset menggunakan Spark SQL...")
    
    # 1. Ubah format returns (wide format) menjadi long format untuk SQL
    # df_returns memiliki kolom Date (index) dan kolom-kolom Aset
    df_long = df_returns.reset_index().melt(id_vars=["Date"], var_name="Asset", value_name="DailyReturn")
    df_long = df_long.dropna()
    
    # 2. Buat Spark DataFrame
    schema = StructType([
        StructField("Date", StringType(), True),
        StructField("Asset", StringType(), True),
        StructField("DailyReturn", DoubleType(), True)
    ])
    
    # Mengonversi Date ke string untuk kemudahan transfer data ke Spark
    df_long["Date"] = df_long["Date"].astype(str)
    spark_df = spark.createDataFrame(df_long, schema=schema)
    
    # 3. Register as SQL Temp View
    spark_df.createOrReplaceTempView("daily_returns")
    
    # 4. Jalankan SQL Query untuk menghitung expected return dan variance (disetahunkan dengan faktor 252 hari bursa)
    query = """
        SELECT 
            Asset, 
            AVG(DailyReturn) * 252 AS expected_return, 
            VAR_SAMP(DailyReturn) * 252 AS variance,
            STDDEV_SAMP(DailyReturn) * SQRT(252) AS volatility
        FROM 
            daily_returns 
        GROUP BY 
            Asset
    """
    result_df = spark.sql(query).toPandas()
    logger.info("Statistik aset berhasil dihitung via Spark SQL.")
    return result_df

def calculate_portfolio_metrics(w: np.ndarray, mu: np.ndarray, Sigma: np.ndarray, P_rel: np.ndarray, rf_rate: float) -> tuple[float, float, float, float]:
    """
    Fungsi bantu untuk menghitung expected return, volatilitas, Sharpe ratio, dan max drawdown dari suatu bobot portofolio.
    Dijalankan di worker node.
    """
    # Expected Return: w^T * mu
    port_return = float(np.dot(w, mu))
    
    # Volatility: sqrt(w^T * Sigma * w)
    port_var = float(np.dot(w.T, np.dot(Sigma, w)))
    port_vol = float(np.sqrt(port_var)) if port_var > 0 else 0.0
    
    # Sharpe Ratio: (Return - Rf) / Volatility
    sharpe = (port_return - rf_rate) / port_vol if port_vol > 0 else -99.0
    
    # Max Drawdown: hitung dari pergerakan harga historis relatif (P_rel)
    # P_rel adalah matriks T x M (baris hari, kolom aset)
    # Nilai portofolio setiap hari: V_t = P_rel * w
    port_values = np.dot(P_rel, w)
    
    # Cari drawdown maksimum
    cum_max = np.maximum.accumulate(port_values)
    drawdowns = (cum_max - port_values) / cum_max
    max_dd = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0
    
    return port_return, port_vol, sharpe, max_dd

def evaluate_portfolios_rdd(
    spark: SparkSession, 
    portfolios: list[np.ndarray], 
    mu: np.ndarray, 
    Sigma: np.ndarray, 
    P_rel: np.ndarray, 
    constraints: dict, 
    rf_rate: float
) -> tuple[list[tuple], tuple]:
    """
    Evaluasi populasi portofolio secara paralel menggunakan PySpark RDD (map, filter, reduce).
    
    Returns:
        evaluated_list: List hasil evaluasi semua portofolio yang lolos constraint.
        best_portfolio: Portofolio terbaik (bobot, return, vol, sharpe, max_dd) berdasarkan RDD reduce.
    """
    # 1. Broadcast variabel-variabel besar ke seluruh worker node
    sc = spark.sparkContext
    b_mu = sc.broadcast(mu)
    b_Sigma = sc.broadcast(Sigma)
    b_P_rel = sc.broadcast(P_rel)
    b_rf = sc.broadcast(rf_rate)
    b_constraints = sc.broadcast(constraints)
    
    # 2. Parallelize populasi portofolio (bobot) menjadi RDD
    # Kita bagi menjadi beberapa partisi (misal 4 atau sesuai core CPU)
    num_partitions = max(4, sc.defaultParallelism)
    rdd_weights = sc.parallelize(portfolios, num_partitions)
    
    # 3. RDD MAP: Hitung Sharpe Ratio & Metrik lainnya untuk tiap kombinasi portofolio
    # Input: w (weights) -> Output: (w, return, volatility, sharpe, max_drawdown)
    def map_metrics(w):
        ret, vol, sharpe, max_dd = calculate_portfolio_metrics(
            w, b_mu.value, b_Sigma.value, b_P_rel.value, b_rf.value
        )
        return (w, ret, vol, sharpe, max_dd)
        
    rdd_metrics = rdd_weights.map(map_metrics)
    
    # 4. RDD FILTER: Buang portofolio yang tidak memenuhi constraint profil risiko
    # Constraints: max_saham, min_fixed, max_drawdown
    def filter_constraints(item):
        w, ret, vol, sharpe, max_dd = item
        cons = b_constraints.value
        
        # Bobot Saham: diasumsikan aset indeks 2 dst adalah saham/emas
        # Bobot Deposito (indeks 0) dan SBN (indeks 1) adalah fixed income
        fixed_weight = w[0] + w[1]
        saham_weight = sum(w[2:]) # Saham + Emas dihitung dalam kategori risiko dinamis/saham
        
        if saham_weight > cons.get("max_saham", 1.0):
            return False
        if fixed_weight < cons.get("min_fixed", 0.0):
            return False
        if max_dd > cons.get("max_drawdown", 1.0):
            return False
            
        return True

    rdd_filtered = rdd_metrics.filter(filter_constraints)
    
    # Cache RDD terfilter karena kita akan melakukan collect dan reduce
    rdd_filtered.cache()
    
    # Ambil semua hasil portofolio yang valid ke driver
    evaluated_list = rdd_filtered.collect()
    
    # 5. RDD REDUCE: Cari portofolio terbaik dengan Sharpe Ratio tertinggi
    best_portfolio = None
    if not rdd_filtered.isEmpty():
        # Membandingkan Sharpe Ratio (indeks ke-3)
        best_portfolio = rdd_filtered.reduce(lambda a, b: a if a[3] > b[3] else b)
    
    # Unpersist dan bersihkan broadcast
    rdd_filtered.unpersist()
    b_mu.unpersist()
    b_Sigma.unpersist()
    b_P_rel.unpersist()
    b_rf.unpersist()
    b_constraints.unpersist()
    
    return evaluated_list, best_portfolio
