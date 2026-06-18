from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os
import pandas as pd
import numpy as np
from backend.orchestrator import optimize_portfolio_flow
from backend.benchmark.runner import run_benchmark
from backend.data.cache import load_prices_cache, load_rates_cache
from backend.pyspark.session import stop_spark_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OptiGene API Server",
    description="Backend API for the OptiGene Portfolio Optimizer using Genetic Algorithm, PySpark, and CUDA."
)

# Add CORS Middleware so that the backend can be accessed from the frontend domain (e.g. Next.js on port 3000 or AWS EC2)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OptimizeRequest(BaseModel):
    capital: float = 5000000.0
    profile: str = "balanced"
    duration: int = 3
    mode: str = "numpy_vectorized"

@app.get("/")
def read_root():
    """
    Status endpoint to verify that the server is running.
    """
    return {
        "status": "online",
        "message": "OptiGene API Server is running. Access the frontend via Next.js dev server on port 3000 or your AWS instance."
    }

@app.post("/api/optimize")
def api_optimize(req: OptimizeRequest):
    """
    Endpoint to compute optimal portfolio allocation based on capital and risk profile.
    """
    try:
        capital = req.capital
        profile = req.profile.lower().strip()
        duration = req.duration
        mode = req.mode.lower().strip()
        
        result = optimize_portfolio_flow(capital, profile, duration, mode=mode)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Error on /api/optimize: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/benchmark")
@app.get("/api/benchmark")
def api_benchmark():
    """
    Endpoint to trigger the performance benchmarking comparing 6 portfolio evaluation methods.
    """
    try:
        logger.info("Received request for performance benchmark...")
        
        # Retrieve data from cache
        df_prices = load_prices_cache()
        rates = load_rates_cache()
        if df_prices.empty or not rates:
            logger.info("Cache is empty, triggering initial data fetch...")
            optimize_portfolio_flow(5000000.0, "balanced", 1, mode="numpy_vectorized")
            df_prices = load_prices_cache()
            rates = load_rates_cache()
            
        bi_rate = rates["bi_rate"]
        sbn_rate = rates["sbn_rate"]
        
        # Calculate daily returns
        df_returns_dynamic = df_prices.pct_change().dropna()
        T_ret = len(df_returns_dynamic)
        
        deposito_daily_ret = bi_rate / 252.0
        sbn_daily_ret = sbn_rate / 252.0
        
        df_returns = pd.DataFrame(index=df_returns_dynamic.index)
        df_returns["DEPOSITO"] = np.full(T_ret, deposito_daily_ret)
        df_returns["SBN ORI"] = np.full(T_ret, sbn_daily_ret)
        
        for col in df_returns_dynamic.columns:
            df_returns[col] = df_returns_dynamic[col]
            
        asset_names = df_returns.columns.tolist()
        
        # Expected return
        mu = df_returns.mean().values * 252.0
        mu[0] = bi_rate
        mu[1] = sbn_rate
        
        # Covariance
        Sigma = np.cov(df_returns.values, rowvar=False) * 252.0
        
        # Price relative path
        P_rel = np.zeros((T_ret + 1, len(asset_names)))
        P_rel[0, :] = 1.0
        for t in range(1, T_ret + 1):
            P_rel[t, 0] = (1.0 + deposito_daily_ret) ** t
            P_rel[t, 1] = (1.0 + sbn_daily_ret) ** t
            
        for col_idx, col_name in enumerate(asset_names[2:], start=2):
            initial_price = df_prices[col_name].iloc[0]
            if initial_price > 0:
                prices_rel = df_prices[col_name].values / initial_price
                P_rel[:, col_idx] = prices_rel[:T_ret+1]
            else:
                P_rel[:, col_idx] = 1.0

        # Run benchmark
        df_benchmark = run_benchmark(df_prices, mu, Sigma, P_rel, profile_name="balanced")
        
        benchmark_list = df_benchmark.to_dict(orient="records")
        return {
            "status": "success",
            "data": benchmark_list
        }
    except Exception as e:
        logger.error(f"Error on /api/benchmark: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Spark cleanup handler when processes are terminated
@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down API server...")
    stop_spark_session()
