import numpy as np
import logging

logger = logging.getLogger(__name__)

try:
    import cupy as cp
except ImportError:
    cp = None

CUDA_CODE = """
extern "C" {

// Random Number Generator
__device__ float rand_float(unsigned int* seed) {
    *seed = (*seed * 1103515245 + 12345);
    return (float)(*seed) / (float)4294967295.0f;
}

// Box-Muller transform to generate standard normally distributed random numbers
__device__ float rand_normal(unsigned int* seed) {
    float u1 = rand_float(seed);
    float u2 = rand_float(seed);
    if (u1 < 1e-6f) u1 = 1e-6f; // prevent log(0)
    return sqrtf(-2.0f * logf(u1)) * cosf(2.0f * 3.14159265f * u2);
}

// 1. Covariance Matrix Kernel (Grid 2D)
__global__ void covariance_kernel(const float* R, const float* means, float* Sigma, int T, int N) {
    int i = blockIdx.x * blockDim.x + threadIdx.x; // Row (asset i)
    int j = blockIdx.y * blockDim.y + threadIdx.y; // Column (asset j)
    
    if (i < N && j < N) {
        float sum = 0.0f;
        float mean_i = means[i];
        float mean_j = means[j];
        for (int t = 0; t < T; ++t) {
            float diff_i = R[t * N + i] - mean_i;
            float diff_j = R[t * N + j] - mean_j;
            sum += diff_i * diff_j;
        }
        // Annualized by multiplying with 252 trading days
        Sigma[i * N + j] = (sum / (float)(T - 1)) * 252.0f;
    }
}

// 2. Portfolio Evaluation Kernel (Grid 1D)
__global__ void evaluate_portfolios_kernel(
    const float* W, const float* mu, const float* Sigma, 
    float* returns, float* volatilities, float* sharpe_ratios, 
    float rf_rate, int P, int N
) {
    int p = blockIdx.x * blockDim.x + threadIdx.x; // Portfolio index
    if (p < P) {
        // expected return = sum(w_k * mu_k)
        float ret = 0.0f;
        for (int k = 0; k < N; ++k) {
            ret += W[p * N + k] * mu[k];
        }
        
        // variance = w^T * Sigma * w
        float var = 0.0f;
        for (int a = 0; a < N; ++a) {
            float temp = 0.0f;
            for (int b = 0; b < N; ++b) {
                temp += W[p * N + b] * Sigma[a * N + b];
            }
            var += W[p * N + a] * temp;
        }
        
        float vol = (var > 0.0f) ? sqrtf(var) : 0.0f;
        float sharpe = (vol > 0.0f) ? ((ret - rf_rate) / vol) : -99.0f;
        
        returns[p] = ret;
        volatilities[p] = vol;
        sharpe_ratios[p] = sharpe;
    }
}

// 3. Monte Carlo Simulation Kernel (Grid 1D)
__global__ void monte_carlo_simulation_kernel(
    float start_val, float ret, float vol, float* paths, 
    int num_sims, int num_days, unsigned int base_seed
) {
    int sim_idx = blockIdx.x * blockDim.x + threadIdx.x; // Simulation path index
    if (sim_idx < num_sims) {
        unsigned int seed = base_seed + sim_idx;
        float dt = 1.0f / 252.0f; // daily time step
        float current_val = start_val;
        paths[sim_idx * num_days + 0] = current_val;
        
        float drift = (ret - 0.5f * vol * vol) * dt;
        float diffusion = vol * sqrtf(dt);
        
        for (int d = 1; d < num_days; ++d) {
            float z = rand_normal(&seed);
            current_val = current_val * expf(drift + diffusion * z);
            paths[sim_idx * num_days + d] = current_val;
        }
    }
}

}
"""

try:
    if cp is None:
        raise ImportError("CuPy is not installed.")
    module = cp.RawModule(code=CUDA_CODE)
    cov_kernel = module.get_function("covariance_kernel")
    eval_kernel = module.get_function("evaluate_portfolios_kernel")
    mc_kernel = module.get_function("monte_carlo_simulation_kernel")
    logger.info("CUDA kernels compiled successfully via CuPy.")
    CUDA_AVAILABLE = True
except Exception as e:
    logger.error(f"Failed to compile CUDA kernels: {e}")
    CUDA_AVAILABLE = False
    cov_kernel = None
    eval_kernel = None
    mc_kernel = None

def gpu_compute_covariance(df_returns: np.ndarray, means: np.ndarray) -> np.ndarray:
    """
    Computes the annualized covariance matrix on the GPU.
    """
    if not CUDA_AVAILABLE:
        raise RuntimeError("CUDA is not available. Use CPU fallback.")
        
    T, N = df_returns.shape

    d_R = cp.asarray(df_returns, dtype=cp.float32)
    d_means = cp.asarray(means, dtype=cp.float32)
    d_Sigma = cp.zeros((N, N), dtype=cp.float32)

    threads_per_block = (16, 16)
    blocks_per_grid = (
        int((N + 15) / 16),
        int((N + 15) / 16)
    )
    
    # Execute covariance kernel
    cov_kernel(blocks_per_grid, threads_per_block, (d_R, d_means, d_Sigma, T, N))
    
    return cp.asnumpy(d_Sigma)

def gpu_evaluate_portfolios(
    weights: np.ndarray, 
    mu: np.ndarray, 
    Sigma: np.ndarray, 
    rf_rate: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Evaluates the entire portfolio population in parallel on the GPU.
    """
    if not CUDA_AVAILABLE:
        raise RuntimeError("CUDA is not available. Use CPU fallback.")
        
    P, N = weights.shape
   
    d_W = cp.asarray(weights, dtype=cp.float32)
    d_mu = cp.asarray(mu, dtype=cp.float32)
    d_Sigma = cp.asarray(Sigma, dtype=cp.float32)
    
    d_returns = cp.zeros(P, dtype=cp.float32)
    d_volatilities = cp.zeros(P, dtype=cp.float32)
    d_sharpes = cp.zeros(P, dtype=cp.float32)
    
    # Define explicit 1D grid & thread dimensions
    threads = 256
    blocks = int((P + 255) / 256)
    
    # Execute portfolio evaluation kernel
    eval_kernel(
        (blocks,), (threads,), 
        (d_W, d_mu, d_Sigma, d_returns, d_volatilities, d_sharpes, np.float32(rf_rate), P, N)
    )
    
    # Copy results back to host (CPU)
    return cp.asnumpy(d_returns), cp.asnumpy(d_volatilities), cp.asnumpy(d_sharpes)

def gpu_monte_carlo(
    start_val: float, 
    ret: float, 
    vol: float, 
    num_sims: int = 1000, 
    num_days: int = 252
) -> np.ndarray:
    """
    Runs Monte Carlo simulations on the GPU to project future portfolio values.
    """
    if not CUDA_AVAILABLE:
        raise RuntimeError("CUDA is not available. Use CPU fallback.")
        
    # Allocate output paths matrix on the GPU (num_sims x num_days)
    d_paths = cp.zeros((num_sims, num_days), dtype=cp.float32)
    
    # Configure grid & block dimensions for 1D kernel
    threads = 256
    blocks = int((num_sims + 255) / 256)
    base_seed = np.random.randint(0, 1000000)
    
    # Execute Monte Carlo simulation kernel
    mc_kernel(
        (blocks,), (threads,), 
        (np.float32(start_val), np.float32(ret), np.float32(vol), d_paths, num_sims, num_days, np.uint32(base_seed))
    )
    
    # Copy paths matrix back to host (CPU)
    return cp.asnumpy(d_paths)
