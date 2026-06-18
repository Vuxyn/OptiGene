import numpy as np
import pandas as pd
import time
import os
import logging
from backend.pyspark.session import get_spark_session
from backend.ga.fitness import evaluate_population
from backend.ga.constraints import get_constraints
from backend.pyspark.context import evaluate_portfolios_rdd
from backend.cuda.kernels import CUDA_AVAILABLE

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def evaluate_portfolios_spark_sql(spark, portfolios: np.ndarray, mu: np.ndarray, Sigma: np.ndarray, rf_rate: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Evaluates 1000 portfolios using Spark SQL.
    """
    P, N = portfolios.shape
    
    # 1. Convert portfolios to DataFrame
    # Schema: PortfolioId, AssetIdx, Weight
    rows_w = []
    for p in range(P):
        for n in range(N):
            rows_w.append((int(p), int(n), float(portfolios[p, n])))
    df_w = spark.createDataFrame(rows_w, ["PortfolioId", "AssetIdx", "Weight"])
    df_w.createOrReplaceTempView("weights_tbl")
    
    # 2. Convert expected returns vector (mu) to DataFrame
    rows_mu = [(int(n), float(mu[n])) for n in range(N)]
    df_mu = spark.createDataFrame(rows_mu, ["AssetIdx", "expected_return"])
    df_mu.createOrReplaceTempView("mu_tbl")
    
    # 3. Convert Covariance Matrix (Sigma) to DataFrame
    rows_cov = []
    for r in range(N):
        for c in range(N):
            rows_cov.append((int(r), int(c), float(Sigma[r, c])))
    df_cov = spark.createDataFrame(rows_cov, ["Asset1Idx", "Asset2Idx", "covariance"])
    df_cov.createOrReplaceTempView("cov_tbl")
    
    # 4. Run SQL query to calculate expected returns, volatility, and Sharpe ratios in parallel
    query = f"""
        WITH PortReturns AS (
            SELECT w.PortfolioId, SUM(w.Weight * m.expected_return) AS port_return
            FROM weights_tbl w
            JOIN mu_tbl m ON w.AssetIdx = m.AssetIdx
            GROUP BY w.PortfolioId
        ),
        PortVariance AS (
            SELECT w1.PortfolioId, SUM(w1.Weight * w2.Weight * c.covariance) AS variance
            FROM weights_tbl w1
            JOIN weights_tbl w2 ON w1.PortfolioId = w2.PortfolioId
            JOIN cov_tbl c ON w1.AssetIdx = c.Asset1Idx AND w2.AssetIdx = c.Asset2Idx
            GROUP BY w1.PortfolioId
        )
        SELECT 
            r.PortfolioId, 
            r.port_return, 
            COALESCE(SQRT(v.variance), 0.0) AS volatility, 
            CASE 
                WHEN v.variance > 0.0 THEN (r.port_return - {rf_rate}) / SQRT(v.variance)
                ELSE -99.0
            END AS sharpe_ratio
        FROM PortReturns r
        JOIN PortVariance v ON r.PortfolioId = v.PortfolioId
        ORDER BY r.PortfolioId
    """
    
    # Execute Spark SQL query
    result = spark.sql(query).collect()
    
    # Convert query outputs back into numpy arrays
    rets = np.zeros(P)
    vols = np.zeros(P)
    sharpes = np.zeros(P)
    
    for row in result:
        pid = row["PortfolioId"]
        rets[pid] = row["port_return"]
        vols[pid] = row["volatility"]
        sharpes[pid] = row["sharpe_ratio"]
        
    return rets, vols, sharpes

def run_benchmark(df_prices: pd.DataFrame, mu: np.ndarray, Sigma: np.ndarray, P_rel: np.ndarray, profile_name: str = "balanced") -> pd.DataFrame:
    """
    Compares the computational performance of 6 execution methods for evaluating Sharpe ratios of 1000 portfolios.
    """
    # 1. Initialize Spark Session
    spark = get_spark_session()
    
    # 2. Prepare 1000 random portfolio weights
    np.random.seed(42)
    P = 1000
    N = len(mu)
    portfolios = np.random.rand(P, N)
    for p in range(P):
        # Normalize weights to sum up to 1.0
        portfolios[p] = portfolios[p] / np.sum(portfolios[p])
        
    # Get the risk-free rate using the BI Rate
    rf_rate = mu[0] if mu[0] > 0 else 0.05
    cons = get_constraints(profile_name)
    
    results = []
    
    logger.info(f"--- STARTING 6-METHOD PERFORMANCE BENCHMARK (N={N}, P={P}) ---")
    
    # ==========================================
    # Method 1: Sequential Python (For Loop)
    # ==========================================
    t_start = time.perf_counter()
    rets1, vols1, sharpes1 = evaluate_population(portfolios, mu, Sigma, rf_rate, mode="sequential")
    # Search for the optimal portfolio sequentially
    # Filter by constraints
    best_sharpe1 = -999.0
    best_idx1 = -1
    for i in range(P):
        fixed_w = portfolios[i, 0] + portfolios[i, 1]
        saham_w = np.sum(portfolios[i, 2:])
        # Verify historical maximum drawdown
        port_vals = np.dot(P_rel, portfolios[i])
        cum_max = np.maximum.accumulate(port_vals)
        max_dd = np.max((cum_max - port_vals) / cum_max) if len(port_vals) > 0 else 0.0
        
        if saham_w <= cons["max_saham"] and fixed_w >= cons["min_fixed"] and max_dd <= cons["max_drawdown"]:
            if sharpes1[i] > best_sharpe1:
                best_sharpe1 = sharpes1[i]
                best_idx1 = i
    t_seq = time.perf_counter() - t_start
    best_w1 = portfolios[best_idx1] if best_idx1 != -1 else np.zeros(N)
    logger.info(f"Method 1: Sequential Python completed in {t_seq:.4f} seconds (Best Sharpe: {best_sharpe1:.4f})")
    results.append({"Method": "Sequential Python", "Time (s)": t_seq, "Best Sharpe": best_sharpe1})
    
    # ==========================================
    # Method 2: PySpark SQL Query
    # ==========================================
    t_start = time.perf_counter()
    rets2, vols2, sharpes2 = evaluate_portfolios_spark_sql(spark, portfolios, mu, Sigma, rf_rate)
    # Search for the optimal portfolio
    best_sharpe2 = -999.0
    best_idx2 = -1
    for i in range(P):
        fixed_w = portfolios[i, 0] + portfolios[i, 1]
        saham_w = np.sum(portfolios[i, 2:])
        port_vals = np.dot(P_rel, portfolios[i])
        cum_max = np.maximum.accumulate(port_vals)
        max_dd = np.max((cum_max - port_vals) / cum_max) if len(port_vals) > 0 else 0.0
        
        if saham_w <= cons["max_saham"] and fixed_w >= cons["min_fixed"] and max_dd <= cons["max_drawdown"]:
            if sharpes2[i] > best_sharpe2:
                best_sharpe2 = sharpes2[i]
                best_idx2 = i
    t_sql = time.perf_counter() - t_start
    best_w2 = portfolios[best_idx2] if best_idx2 != -1 else np.zeros(N)
    logger.info(f"Method 2: PySpark SQL Query completed in {t_sql:.4f} seconds (Best Sharpe: {best_sharpe2:.4f})")
    results.append({"Method": "PySpark SQL Query", "Time (s)": t_sql, "Best Sharpe": best_sharpe2})
 
    # ==========================================
    # Method 3: PySpark RDD map
    # ==========================================
    t_start = time.perf_counter()
    rets3, vols3, sharpes3 = evaluate_population(portfolios, mu, Sigma, rf_rate, mode="pyspark_cpu", spark=spark)
    best_sharpe3 = -999.0
    best_idx3 = -1
    for i in range(P):
        fixed_w = portfolios[i, 0] + portfolios[i, 1]
        saham_w = np.sum(portfolios[i, 2:])
        port_vals = np.dot(P_rel, portfolios[i])
        cum_max = np.maximum.accumulate(port_vals)
        max_dd = np.max((cum_max - port_vals) / cum_max) if len(port_vals) > 0 else 0.0
        
        if saham_w <= cons["max_saham"] and fixed_w >= cons["min_fixed"] and max_dd <= cons["max_drawdown"]:
            if sharpes3[i] > best_sharpe3:
                best_sharpe3 = sharpes3[i]
                best_idx3 = i
    t_rdd_map = time.perf_counter() - t_start
    best_w3 = portfolios[best_idx3] if best_idx3 != -1 else np.zeros(N)
    logger.info(f"Method 3: PySpark RDD map completed in {t_rdd_map:.4f} seconds (Best Sharpe: {best_sharpe3:.4f})")
    results.append({"Method": "PySpark RDD map", "Time (s)": t_rdd_map, "Best Sharpe": best_sharpe3})
 
    # ==========================================
    # Method 4: PySpark RDD filter + reduce
    # ==========================================
    t_start = time.perf_counter()
    # Directly use RDD functions inside pyspark/context.py
    valid_list, rdd_best = evaluate_portfolios_rdd(spark, portfolios, mu, Sigma, P_rel, cons, rf_rate)
    t_rdd_fr = time.perf_counter() - t_start
    best_sharpe4 = rdd_best[3] if rdd_best is not None else -999.0
    best_w4 = rdd_best[0] if rdd_best is not None else np.zeros(N)
    logger.info(f"Method 4: PySpark RDD filter+reduce completed in {t_rdd_fr:.4f} seconds (Best Sharpe: {best_sharpe4:.4f})")
    results.append({"Method": "PySpark RDD filter + reduce", "Time (s)": t_rdd_fr, "Best Sharpe": best_sharpe4})
 
    # ==========================================
    # Method 5: Pure CUDA (GPU)
    # ==========================================
    t_start = time.perf_counter()
    # Execute on GPU via CuPy
    if CUDA_AVAILABLE:
        rets5, vols5, sharpes5 = evaluate_population(portfolios, mu, Sigma, rf_rate, mode="cuda")
        best_sharpe5 = -999.0
        best_idx5 = -1
        for i in range(P):
            fixed_w = portfolios[i, 0] + portfolios[i, 1]
            saham_w = np.sum(portfolios[i, 2:])
            port_vals = np.dot(P_rel, portfolios[i])
            cum_max = np.maximum.accumulate(port_vals)
            max_dd = np.max((cum_max - port_vals) / cum_max) if len(port_vals) > 0 else 0.0
            
            if saham_w <= cons["max_saham"] and fixed_w >= cons["min_fixed"] and max_dd <= cons["max_drawdown"]:
                if sharpes5[i] > best_sharpe5:
                    best_sharpe5 = sharpes5[i]
                    best_idx5 = i
        t_cuda = time.perf_counter() - t_start
        best_w5 = portfolios[best_idx5] if best_idx5 != -1 else np.zeros(N)
        logger.info(f"Method 5: Pure CUDA completed in {t_cuda:.4f} seconds (Best Sharpe: {best_sharpe5:.4f})")
    else:
        logger.warning("Method 5 (Pure CUDA GPU) skipped due to missing CUDA resources.")
        t_cuda = np.nan
        best_sharpe5 = np.nan
        best_w5 = np.zeros(N)
    results.append({"Method": "Pure CUDA (GPU)", "Time (s)": t_cuda, "Best Sharpe": best_sharpe5})
 
    # ==========================================
    # Method 6: PySpark + CUDA (Hybrid)
    # ==========================================
    t_start = time.perf_counter()
    rets6, vols6, sharpes6 = evaluate_population(portfolios, mu, Sigma, rf_rate, mode="pyspark_cuda", spark=spark)
    best_sharpe6 = -999.0
    best_idx6 = -1
    for i in range(P):
        fixed_w = portfolios[i, 0] + portfolios[i, 1]
        saham_w = np.sum(portfolios[i, 2:])
        port_vals = np.dot(P_rel, portfolios[i])
        cum_max = np.maximum.accumulate(port_vals)
        max_dd = np.max((cum_max - port_vals) / cum_max) if len(port_vals) > 0 else 0.0
        
        if saham_w <= cons["max_saham"] and fixed_w >= cons["min_fixed"] and max_dd <= cons["max_drawdown"]:
            if sharpes6[i] > best_sharpe6:
                best_sharpe6 = sharpes6[i]
                best_idx6 = i
    t_hybrid = time.perf_counter() - t_start
    best_w6 = portfolios[best_idx6] if best_idx6 != -1 else np.zeros(N)
    logger.info(f"Method 6: PySpark + CUDA hybrid completed in {t_hybrid:.4f} seconds (Best Sharpe: {best_sharpe6:.4f})")
    results.append({"Method": "PySpark + CUDA", "Time (s)": t_hybrid, "Best Sharpe": best_sharpe6})
 
    # ==========================================
    # Verify Numerical Output Consistency
    # ==========================================
    logger.info("--- STARTING NUMERICAL CONSISTENCY VERIFICATION ---")
    valid_sharpes = [best_sharpe1, best_sharpe2, best_sharpe3, best_sharpe4, best_sharpe6]
    if CUDA_AVAILABLE:
        valid_sharpes.append(best_sharpe5)
        
    diff = max(valid_sharpes) - min(valid_sharpes)
    logger.info(f"Maximum Sharpe Ratio difference across methods: {diff:.8f}")
    if diff < 1e-4:
        logger.info("VERIFICATION SUCCESS: All execution methods yielded identical optimal Sharpe ratios! ✅")
    else:
        logger.warning("VERIFICATION WARNING: Significant numerical discrepancies found between methods.")
 
    # 3. Calculate Speedup
    df_res = pd.DataFrame(results)
    df_res["Speedup"] = df_res["Time (s)"].iloc[0] / df_res["Time (s)"]
    
    # 4. Save results to CSV cache
    res_dir = "d:/INFORMATICS/SEMESTER 4/PARALLEL PROCESSING/Spark/backend/results"
    if not os.path.exists(res_dir):
        os.makedirs(res_dir)
    csv_path = os.path.join(res_dir, "benchmark.csv")
    df_res.to_csv(csv_path, index=False)
    logger.info(f"Benchmark results successfully written to: {csv_path}")
    
    return df_res
