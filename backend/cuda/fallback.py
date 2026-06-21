import numpy as np
import logging

logger = logging.getLogger(__name__)

def cpu_compute_covariance(df_returns: np.ndarray, means: np.ndarray) -> np.ndarray:

    logger.info("Running compute_covariance on CPU...")
    # T, N = df_returns.shape
    # Returns values minus their means
    # np.cov automatically computes the sample covariance (divided by T-1)
    cov_matrix = np.cov(df_returns, rowvar=False) * 252.0
    
    # If only 1 asset, np.cov returns a scalar. Convert it to a 2D array.
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
    Evaluates the portfolio population on the CPU in a vectorized manner using NumPy.
    """
    # Expected Return: R = W * mu
    returns = np.dot(weights, mu)
    
    # Variance: for each row w, compute w^T * Sigma * w
    # W * Sigma yields a matrix of shape P x N
    # Multiply element-wise with W, then sum across rows (axis=1) to get the variances
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

    dt = 1.0 / 252.0
    drift = (ret - 0.5 * vol * vol) * dt
    diffusion = vol * np.sqrt(dt)
    
    # Generate random normal variables
    z = np.random.normal(size=(num_sims, num_days - 1))
    
    # Calculate exponential changes
    path_changes = np.exp(drift + diffusion * z)
    
    # Create paths array and calculate cumulative product
    paths = np.zeros((num_sims, num_days), dtype=np.float32)
    paths[:, 0] = start_val
    paths[:, 1:] = start_val * np.cumprod(path_changes, axis=1)
    
    return paths
