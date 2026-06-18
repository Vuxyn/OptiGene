import numpy as np
import logging

logger = logging.getLogger(__name__)

def cpu_compute_covariance(df_returns: np.ndarray, means: np.ndarray) -> np.ndarray:
    """
    Menghitung matriks kovarians yang disetahunkan menggunakan CPU (NumPy).
    """
    logger.info("Menjalankan compute_covariance di CPU...")
    # T, N = df_returns.shape
    # Baris data return dikurangi rata-ratanya
    # np.cov menghitung covariance sample secara otomatis (dibagi T-1)
    cov_matrix = np.cov(df_returns, rowvar=False) * 252.0
    
    # Jika hanya 1 aset, np.cov mengembalikan scalar. Ubah jadi 2D array.
    if np.isscalar(cov_matrix):
        cov_matrix = np.array([[cov_matrix]])
    elif cov_matrix.ndim == 0:
        cov_matrix = cov_matrix.reshape(1, 1)
        
    return cov_matrix

def cpu_evaluate_portfolios(
    weights: np.ndarray, 
    mu: np.ndarray, 
    Sigma: np.ndarray, 
    rf_rate: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Mengevaluasi populasi portofolio di CPU secara vektor menggunakan NumPy.
    """
    # Expected Return: R = W * mu
    returns = np.dot(weights, mu)
    
    # Variance: untuk setiap baris w, hitung w^T * Sigma * w
    # W * Sigma menghasilkan matriks P x N
    # Kalikan secara element-wise dengan W lalu jumlahkan tiap baris (axis=1) untuk mendapatkan variansi
    variances = np.sum(np.dot(weights, Sigma) * weights, axis=1)
    
    volatilities = np.sqrt(np.maximum(variances, 0.0))
    
    # Sharpe Ratio: (R - Rf) / Vol
    sharpe_ratios = np.where(volatilities > 0.0, (returns - rf_rate) / volatilities, -99.0)
    
    return returns, volatilities, sharpe_ratios

def cpu_monte_carlo(
    start_val: float, 
    ret: float, 
    vol: float, 
    num_sims: int = 1000, 
    num_days: int = 252
) -> np.ndarray:
    """
    Simulasi Monte Carlo di CPU menggunakan NumPy (Geometric Brownian Motion).
    """
    dt = 1.0 / 252.0
    drift = (ret - 0.5 * vol * vol) * dt
    diffusion = vol * np.sqrt(dt)
    
    # Generate random normal variables
    z = np.random.normal(size=(num_sims, num_days - 1))
    
    # Hitung pergerakan eksponensial
    path_changes = np.exp(drift + diffusion * z)
    
    # Buat array paths dan hitung cumulative product
    paths = np.zeros((num_sims, num_days), dtype=np.float32)
    paths[:, 0] = start_val
    paths[:, 1:] = start_val * np.cumprod(path_changes, axis=1)
    
    return paths
