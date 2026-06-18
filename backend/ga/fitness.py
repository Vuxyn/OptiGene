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
    spark = None
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Evaluasi populasi portofolio berdasarkan backend terpilih.
    
    Args:
        population: np.ndarray berukuran (P, N) di mana P adalah populasi, N jumlah aset.
        mu: expected returns per aset (N,)
        Sigma: covariance matrix (N, N)
        rf_rate: risk-free interest rate (BI rate)
        mode: "sequential", "numpy_vectorized", "cuda", "pyspark_cpu", "pyspark_cuda"
        spark: SparkSession aktif (diperlukan jika menggunakan mode PySpark)
        
    Returns:
        returns: (P,) expected returns portofolio
        volatilities: (P,) volatilitas portofolio
        sharpes: (P,) fitness/Sharpe ratio portofolio
    """
    mode_clean = mode.lower().strip()
    P, N = population.shape

    if mode_clean == "sequential":
        # Loop standar Python murni tanpa vektorisasi NumPy (untuk baseline benchmark sekuensial)
        returns = np.zeros(P)
        volatilities = np.zeros(P)
        sharpes = np.zeros(P)
        
        for p in range(P):
            w = population[p]
            # 1. Expected Return
            ret = 0.0
            for k in range(N):
                ret += w[k] * mu[k]
            
            # 2. Volatilitas
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
        # Vektorisasi CPU dengan NumPy (Fallback cepat)
        return cpu_evaluate_portfolios(population, mu, Sigma, rf_rate)

    elif mode_clean == "cuda":
        # GPU Acceleration dengan CuPy
        if CUDA_AVAILABLE:
            try:
                return gpu_evaluate_portfolios(population, mu, Sigma, rf_rate)
            except Exception as e:
                logger.error(f"Gagal evaluasi via CUDA GPU: {e}. Melakukan fallback ke NumPy.")
                return cpu_evaluate_portfolios(population, mu, Sigma, rf_rate)
        else:
            logger.warning("CUDA tidak tersedia pada environment ini. Menggunakan NumPy.")
            return cpu_evaluate_portfolios(population, mu, Sigma, rf_rate)

    elif mode_clean == "pyspark_cpu":
        # Parallel RDD map di CPU
        if spark is None:
            raise ValueError("SparkSession harus disertakan untuk mode pyspark_cpu")
        
        # Parallelize dan hitung menggunakan RDD map
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

        # Collect hasil
        results = rdd_weights.map(map_pyspark_metrics).collect()
        
        # Bersihkan broadcast
        b_mu.unpersist()
        b_Sigma.unpersist()
        b_rf.unpersist()
        
        # Ubah list of tuple menjadi array numpy
        results_arr = np.array(results)
        return results_arr[:, 0], results_arr[:, 1], results_arr[:, 2]

    elif mode_clean == "pyspark_cuda":
        # Hybrid: RDD mapPartitions + CuPy di GPU (sangat scalable)
        if spark is None:
            raise ValueError("SparkSession harus disertakan untuk mode pyspark_cuda")
            
        sc = spark.sparkContext
        b_mu = sc.broadcast(mu)
        b_Sigma = sc.broadcast(Sigma)
        b_rf = sc.broadcast(rf_rate)
        
        rdd_weights = sc.parallelize(population.tolist(), max(4, sc.defaultParallelism))
        
        def map_partition_cuda_eval(iterator):
            weights_list = list(iterator)
            if not weights_list:
                return []
            
            # Konversi menjadi numpy array untuk evaluasi kelompok (chunk)
            weights_arr = np.array(weights_list)
            
            # Coba impor CuPy di worker node
            try:
                import cupy as cp
                
                # Import kernels secara dinamis
                from backend.cuda.kernels import gpu_evaluate_portfolios
                rets, vols, sharpes = gpu_evaluate_portfolios(
                    weights_arr, b_mu.value, b_Sigma.value, b_rf.value
                )
                # Kembalikan sebagai list of tuple
                return list(zip(rets.tolist(), vols.tolist(), sharpes.tolist()))
            except Exception as ex:
                # Fallback ke CPU numpy jika worker tidak memiliki GPU/CuPy
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

    else:
        raise ValueError(f"Mode evaluasi tidak dikenali: {mode}")
