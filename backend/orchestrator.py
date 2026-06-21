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
    Coordinates the entire OptiGene workflow: fetching data,
    calculating asset statistics, executing the Genetic Algorithm, and formatting output.
    """
    logger.info("Starting OptiGene portfolio optimization workflow...")
    
    # 1. Fetch or Load Interest Rates (BI Rate & SBN)
    rates = load_rates_cache()
    if not rates:
        bi_rate = fetch_bi_rate()
        sbn_rate = fetch_sbn_rate()
        rates = {"bi_rate": bi_rate, "sbn_rate": sbn_rate}
        save_rates_cache(rates)
    else:
        bi_rate = rates["bi_rate"]
        sbn_rate = rates["sbn_rate"]
        
    # 2. Fetch or Load Historical Asset Prices (Stocks & Gold, 2022 - 2024)
    df_prices = load_prices_cache()
    if df_prices.empty:
        # Fetch Gold (ANTM.JK)
        s_gold = fetch_gold_prices()
        # Fetch LQ45 Stocks
        df_stocks = fetch_asset_prices(LQ45_TICKERS)
        
        # Combine
        if not s_gold.empty:
            df_stocks["GOLD"] = s_gold
            
        df_prices = df_stocks
        
        # Validate Assets (listing > 3 years, data coverage >= 95%)
        df_prices, valid_tickers = validate_assets(df_prices, min_coverage=0.95)
        
        # Save to cache if successful
        if not df_prices.empty:
            save_prices_cache(df_prices)
    else:
        valid_tickers = df_prices.columns.tolist()

    if df_prices.empty:
        raise RuntimeError("Failed to load valid historical asset prices.")

    # 3. Calculate Daily Returns for Dynamic Assets (Stocks & Gold)
    df_returns_dynamic = df_prices.pct_change().dropna()
    
    # 4. Integrate Fixed Income Assets (Time Deposits & SBN)
    # Time Deposits have constant daily return = bi_rate / 252
    # SBN has constant daily return = sbn_rate / 252
    T = len(df_returns_dynamic)
    
    deposito_daily_ret = bi_rate / 252.0
    sbn_daily_ret = sbn_rate / 252.0
    
    # Create complete returns DataFrame (Time Deposit, SBN, Gold, Stocks)
    df_returns = pd.DataFrame(index=df_returns_dynamic.index)
    df_returns["DEPOSITO"] = np.full(T, deposito_daily_ret)
    df_returns["SBN ORI"] = np.full(T, sbn_daily_ret)
    
    for col in df_returns_dynamic.columns:
        df_returns[col] = df_returns_dynamic[col]
        
    # Name all assets in order
    asset_names = df_returns.columns.tolist()
    N = len(asset_names)
    
    # 5. Compute Asset Statistics (Expected Return & Covariance)
    # Use Spark SQL to calculate historical stats if Spark is enabled
    # (Optional / Can CPU fallback for fast initialization)
    spark = None
    if "pyspark" in mode.lower():
        try:
            spark = get_spark_session()
            df_stats_sql = compute_asset_stats_sql(spark, df_returns)
            
            # Map SQL result to expected return array (mu)
            mu_dict = dict(zip(df_stats_sql["Asset"], df_stats_sql["expected_return"]))
            mu = np.array([mu_dict.get(asset, 0.0) for asset in asset_names])
        except Exception as e:
            logger.error(f"Failed to calculate stats via Spark SQL: {e}. Using NumPy on CPU.")
            # Fallback to CPU expected return
            mu = df_returns.mean().values * 252.0
    else:
        # NumPy CPU expected return
        mu = df_returns.mean().values * 252.0
        
    # For Time Deposit and SBN, force their expected returns to match annual interest rates
    mu[0] = bi_rate
    mu[1] = sbn_rate
    
    # Compute covariance matrix (annualized)
    # Covariance of Time Deposit and SBN with other assets is 0 since they are constant
    # We calculate via NumPy CPU (fast) or GPU if CuPy is enabled and mode="cuda"
    if mode == "cuda":
        from backend.cuda.kernels import gpu_compute_covariance, CUDA_AVAILABLE
        if CUDA_AVAILABLE:
            try:
                means = df_returns.mean().values
                Sigma = gpu_compute_covariance(df_returns.values, means)
            except Exception as e:
                logger.error(f"Failed to calculate covariance on GPU: {e}. Falling back to CPU.")
                Sigma = np.cov(df_returns.values, rowvar=False) * 252.0
        else:
            Sigma = np.cov(df_returns.values, rowvar=False) * 252.0
    else:
        Sigma = np.cov(df_returns.values, rowvar=False) * 252.0
        
    # Clean covariance matrix to ensure no NaN/Inf values
    Sigma = np.nan_to_num(Sigma, nan=0.0, posinf=0.0, neginf=0.0)

    # 6. Calculate Historical Price Relative Paths (P_rel) for Max Drawdown
    # P_rel size: T + 1 x N
    P_rel = np.zeros((T + 1, N))
    
    # Day 0 values are 1.0 (baseline)
    P_rel[0, :] = 1.0
    
    # For Time Deposit & SBN: grow constantly (1 + daily_return)^t
    # For Stocks & Gold: relative prices to initial price
    for t in range(1, T + 1):
        P_rel[t, 0] = (1.0 + deposito_daily_ret) ** t
        P_rel[t, 1] = (1.0 + sbn_daily_ret) ** t
        
    # Dynamic (Stocks & Gold)
    # df_prices includes daily closing prices
    # Find initial price
    for col_idx, col_name in enumerate(asset_names[2:], start=2):
        initial_price = df_prices[col_name].iloc[0]
        # Prevent division by zero
        if initial_price > 0:
            prices_rel = df_prices[col_name].values / initial_price
            # Match length to T + 1
            P_rel[:, col_idx] = prices_rel[:T+1]
        else:
            P_rel[:, col_idx] = 1.0

    # 7. Run Genetic Algorithm Optimizer
    # Default parameters: population size = 500, generations = 150 (fast & converged)
    optimizer = GeneticOptimizer(pop_size=500, generations=150)
    
    # Ensure Spark session is passed to the optimizer if PySpark mode is used
    if "pyspark" in mode.lower() and spark is None:
        spark = get_spark_session()
        
    ga_results = optimizer.run(mu, Sigma, P_rel, risk_profile, mode=mode, spark=spark)
    
    # Add asset names metadata for the formatter
    ga_results["asset_names"] = asset_names
    
    # 8. Format Output to Layman-friendly Terms
    layman_formatted = format_layman_results(ga_results, capital, duration_years)
    
    return layman_formatted
