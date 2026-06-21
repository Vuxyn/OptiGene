import numpy as np
import logging
from backend.cuda.fallback import cpu_evaluate_portfolios
from backend.cuda.kernels import gpu_evaluate_portfolios, CUDA_AVAILABLE

logger = logging.getLogger(__name__)

def evaluate_population(
    population: np.ndarray, 
    mu: np.ndarray, 
    Sigma: np.ndarray, 
    rf_rate: float, 
    mode: str = "sequential",
    spark = None,
    allow_fallback: bool = True
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Evaluates the portfolio population based on the selected execution backend.
    
    Args:
        population: np.ndarray of shape (P, N) where P is the population size and N is the number of assets.
        mu: expected returns per asset (N,)
        Sigma: covariance matrix (N, N)
        rf_rate: risk-free interest rate (BI rate)
        mode: "sequential", "numpy_vectorized", "cuda", "pyspark_cpu", "pyspark_cuda"
        spark: Active SparkSession (required if using PySpark mode)
        
    Returns:
        returns: (P,) expected portfolio returns
        volatilities: (P,) portfolio volatilities
        sharpes: (P,) portfolio fitness/Sharpe ratios
    """
    mode_clean = mode.lower().strip()
    P, N = population.shape

    if mode_clean == "sequential":
        # Pure Python loop without NumPy vectorization (used as baseline benchmark)
        returns = np.zeros(P)
        volatilities = np.zeros(P)
        sharpes = np.zeros(P)
        
        for p in range(P):
            w = population[p]
            # 1. Expected Return
            ret = 0.0
            for k in range(N):
                ret += w[k] * mu[k]
            
            # 2. Volatility
            var = 0.0
            for a in range(N):
                temp = 0.0
                for b in range(N):
                    temp += w[b] * Sigma[a, b]
                var += w[a] * temp
            
            vol = np.sqrt(var) if var > 0 else 0.0
            sharpe = (ret - rf_rate) / vol if vol > 0 else -99.0
            
            returns[p] = ret
            volatilities[p] = vol
            sharpes[p] = sharpe
            
        return returns, volatilities, sharpes

    elif mode_clean == "numpy_vectorized":
        # Vectorized CPU computation using NumPy
        return cpu_evaluate_portfolios(population, mu, Sigma, rf_rate)

    elif mode_clean == "cuda":
        # GPU Acceleration using CuPy
        if CUDA_AVAILABLE:
            try:
                return gpu_evaluate_portfolios(population, mu, Sigma, rf_rate)
            except Exception as e:
                logger.error(f"Failed to evaluate via CUDA GPU: {e}. Falling back to NumPy CPU.")
                if not allow_fallback:
                    raise e
                return cpu_evaluate_portfolios(population, mu, Sigma, rf_rate)
        else:
            logger.warning("CUDA is not available in this environment. Falling back to NumPy CPU.")
            return cpu_evaluate_portfolios(population, mu, Sigma, rf_rate)

    elif mode_clean == "pyspark_cpu":
        # Parallel RDD map execution on CPU
        if spark is None:
            raise ValueError("SparkSession must be provided for pyspark_cpu mode")
        
        try:
            # Parallelize and compute using RDD map
            sc = spark.sparkContext
            b_mu = sc.broadcast(mu)
            b_Sigma = sc.broadcast(Sigma)
            b_rf = sc.broadcast(rf_rate)
            
            rdd_weights = sc.parallelize(population.tolist(), max(4, sc.defaultParallelism))
            
            def map_pyspark_metrics(w_list):
                w = np.array(w_list)
                ret = float(np.dot(w, b_mu.value))
                var = float(np.dot(w.T, np.dot(b_Sigma.value, w)))
                vol = float(np.sqrt(var)) if var > 0 else 0.0
                sharpe = (ret - b_rf.value) / vol if vol > 0 else -99.0
                return ret, vol, sharpe

            # Collect results
            results = rdd_weights.map(map_pyspark_metrics).collect()
            
            b_mu.unpersist()
            b_Sigma.unpersist()
            b_rf.unpersist()
            
            # Convert list of tuples to numpy arrays
            results_arr = np.array(results)
            return results_arr[:, 0], results_arr[:, 1], results_arr[:, 2]
        except Exception as e:
            logger.error(f"PySpark CPU RDD execution failed: {e}. Falling back to NumPy CPU.")
            if not allow_fallback:
                raise e
            return cpu_evaluate_portfolios(population, mu, Sigma, rf_rate)

    elif mode_clean == "pyspark_cuda":
        # Hybrid: RDD mapPartitions + CuPy on GPU
        if spark is None:
            raise ValueError("SparkSession must be provided for pyspark_cuda mode")
            
        try:
            sc = spark.sparkContext
            b_mu = sc.broadcast(mu)
            b_Sigma = sc.broadcast(Sigma)
            b_rf = sc.broadcast(rf_rate)
            
            rdd_weights = sc.parallelize(population.tolist(), max(4, sc.defaultParallelism))
            
            def map_partition_cuda_eval(iterator):
                weights_list = list(iterator)
                if not weights_list:
                    return []
                
                weights_arr = np.array(weights_list)
                try:
                    import cupy as cp
                    
                    from backend.cuda.kernels import gpu_evaluate_portfolios
                    rets, vols, sharpes = gpu_evaluate_portfolios(
                        weights_arr, b_mu.value, b_Sigma.value, b_rf.value
                    )
                    return list(zip(rets.tolist(), vols.tolist(), sharpes.tolist()))
                except Exception as ex:
                    rets, vols, sharpes = cpu_evaluate_portfolios(
                        weights_arr, b_mu.value, b_Sigma.value, b_rf.value
                    )
                    return list(zip(rets.tolist(), vols.tolist(), sharpes.tolist()))

            results = rdd_weights.mapPartitions(map_partition_cuda_eval).collect()
            
            b_mu.unpersist()
            b_Sigma.unpersist()
            b_rf.unpersist()
            
            results_arr = np.array(results)
            return results_arr[:, 0], results_arr[:, 1], results_arr[:, 2]
        except Exception as e:
            logger.error(f"PySpark + CUDA Hybrid execution failed: {e}. Falling back to NumPy CPU.")
            if not allow_fallback:
                raise e
            return cpu_evaluate_portfolios(population, mu, Sigma, rf_rate)

    else:
        raise ValueError(f"Unrecognized evaluation mode: {mode}")
