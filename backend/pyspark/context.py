from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def compute_asset_stats_sql(spark: SparkSession, df_returns: pd.DataFrame) -> pd.DataFrame:
    """
    Uses SparkSession SQL queries to calculate mean annual returns, annual volatility,
    and variance per asset from daily returns data.
    """
    logger.info("Computing asset statistics using Spark SQL...")
    
    # 1. Melt wide returns format into long format for SQL query execution
    # df_returns has Date (index) and Asset columns
    df_long = df_returns.reset_index().melt(id_vars=["Date"], var_name="Asset", value_name="DailyReturn")
    df_long = df_long.dropna()
    
    # 2. Create Spark DataFrame
    schema = StructType([
        StructField("Date", StringType(), True),
        StructField("Asset", StringType(), True),
        StructField("DailyReturn", DoubleType(), True)
    ])
    
    # Convert Date to string to ease data transfer to Spark workers
    df_long["Date"] = df_long["Date"].astype(str)
    spark_df = spark.createDataFrame(df_long, schema=schema)
    
    # 3. Register as SQL Temp View
    spark_df.createOrReplaceTempView("daily_returns")
    
    # 4. Run SQL Query to compute expected returns and variance (annualized by factor of 252 trading days)
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
    logger.info("Asset statistics computed successfully via Spark SQL.")
    return result_df

def calculate_portfolio_metrics(w: np.ndarray, mu: np.ndarray, Sigma: np.ndarray, P_rel: np.ndarray, rf_rate: float) -> tuple[float, float, float, float]:
    """
    Helper function to calculate expected return, volatility, Sharpe ratio, and max drawdown for a portfolio weight vector.
    Executed on worker nodes.
    """
    # Expected Return: w^T * mu
    port_return = float(np.dot(w, mu))
    
    # Volatility: sqrt(w^T * Sigma * w)
    port_var = float(np.dot(w.T, np.dot(Sigma, w)))
    port_vol = float(np.sqrt(port_var)) if port_var > 0 else 0.0
    
    # Sharpe Ratio: (Return - Rf) / Volatility
    sharpe = (port_return - rf_rate) / port_vol if port_vol > 0 else -99.0
    
    # Max Drawdown: calculate from historical price relative paths (P_rel)
    port_values = np.dot(P_rel, w)
    
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

    sc = spark.sparkContext
    b_mu = sc.broadcast(mu)
    b_Sigma = sc.broadcast(Sigma)
    b_P_rel = sc.broadcast(P_rel)
    b_rf = sc.broadcast(rf_rate)
    b_constraints = sc.broadcast(constraints)
    
    # Parallelize the portfolio population list into RDD partitions
    num_partitions = max(4, sc.defaultParallelism)
    rdd_weights = sc.parallelize(portfolios, num_partitions)
    
    def map_metrics(w):
        ret, vol, sharpe, max_dd = calculate_portfolio_metrics(
            w, b_mu.value, b_Sigma.value, b_P_rel.value, b_rf.value
        )
        return (w, ret, vol, sharpe, max_dd)
        
    rdd_metrics = rdd_weights.map(map_metrics)
    
    def filter_constraints(item):
        w, ret, vol, sharpe, max_dd = item
        cons = b_constraints.value
        
        fixed_weight = w[0] + w[1]
        saham_weight = sum(w[2:])
        if saham_weight > cons.get("max_saham", 1.0):
            return False
        if fixed_weight < cons.get("min_fixed", 0.0):
            return False
        if max_dd > cons.get("max_drawdown", 1.0):
            return False
            
        return True

    rdd_filtered = rdd_metrics.filter(filter_constraints)
    
    # Cache filtered RDD as we perform both collect and reduce operations on it
    rdd_filtered.cache()
    
    # Collect valid portfolio statistics back to the driver node
    evaluated_list = rdd_filtered.collect()
    
    # 5. RDD REDUCE: Locate the optimal portfolio containing the maximum Sharpe ratio
    best_portfolio = None
    if not rdd_filtered.isEmpty():
        # Compare Sharpe Ratio values (index 3)
        best_portfolio = rdd_filtered.reduce(lambda a, b: a if a[3] > b[3] else b)
    
    # Clean up RDD caches and broadcast variables
    rdd_filtered.unpersist()
    b_mu.unpersist()
    b_Sigma.unpersist()
    b_P_rel.unpersist()
    b_rf.unpersist()
    b_constraints.unpersist()
    
    return evaluated_list, best_portfolio
