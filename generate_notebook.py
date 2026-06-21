import json
import os

notebook_content = {
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# OptiGene — Jupyter Notebook Demo\n",
    "### Course: Parallel Processing (Komputasi Paralel)\n",
    "\n",
    "This notebook interactively demonstrates the entire **OptiGene** workflow:\n",
    "1. **Data Layer**: Downloading historical prices (yfinance) and web scraping interest rates (BI & SBN).\n",
    "2. **Genetic Algorithm**: Searching for the optimal portfolio weights based on risk profile constraints.\n",
    "3. **Parallel Computing**: Executing performance benchmarks comparing 6 methods (Sequential Python, PySpark SQL, PySpark RDD map, PySpark RDD filter+reduce, CUDA GPU, and PySpark + CUDA hybrid) and visualizing inline *speedup* charts."
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 1. Environment Verification & Module Imports"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "import os\n",
    "import sys\n",
    "import numpy as np\n",
    "import pandas as pd\n",
    "import matplotlib.pyplot as plt\n",
    "\n",
    "# Include workspace root folder in python search path\n",
    "sys.path.append(os.path.abspath(\".\"))\n",
    "\n",
    "from backend.pyspark.session import get_spark_session\n",
    "from backend.cuda.kernels import CUDA_AVAILABLE\n",
    "from backend.orchestrator import optimize_portfolio_flow\n",
    "\n",
    "print(\"=== OPTIGENE ENVIRONMENT STATUS ===\")\n",
    "print(f\"CUDA (GPU via CuPy) Available: {CUDA_AVAILABLE}\")\n",
    "\n",
    "# Inline Spark session initialization\n",
    "spark = get_spark_session()\n",
    "print(f\"PySpark Version: {spark.version}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 2. Data Scraping & Historical Asset Analysis\n",
    "We fetch historical data from yfinance (LQ45 index constituents & gold) and scrape interest rates (latest BI Rate & 10Y SBN yields)."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "from backend.data.fetcher import fetch_bi_rate, fetch_sbn_rate, LQ45_TICKERS\n",
    "from backend.data.cache import load_prices_cache\n",
    "\n",
    "bi_rate = fetch_bi_rate()\n",
    "sbn_rate = fetch_sbn_rate()\n",
    "\n",
    "print(f\"Time Deposit Interest Rate (BI Rate): {bi_rate * 100:.2f}%\")\n",
    "print(f\"Government SBN Bond Yield (10Y): {sbn_rate * 100:.2f}%\")\n",
    "\n",
    "# Load historical price cache\n",
    "df_prices = load_prices_cache()\n",
    "if df_prices.empty:\n",
    "    print(\"Cache is empty, please run optimization flow once to download yfinance historical data.\")\n",
    "else:\n",
    "    print(f\"\\nNumber of Registered Assets: {len(df_prices.columns)} (Gold + LQ45 stocks passing validation)\")\n",
    "    print(\"\\nHistorical Price Sample (First 5 records):\")\n",
    "    display(df_prices.head())"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 3. Portfolio Optimization Execution (Genetic Algorithm)\n",
    "We run the Genetic Algorithm search to find the optimal portfolio allocation. We will run it for both **Safe (Conservative)** and **Aggressive** risk profiles."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "capital = 10000000.0 # Capital: IDR 10,000,000\n",
    "\n",
    "# 1. Safe (Conservative) Risk Profile (Max Stock allocation 20%)\n",
    "print(\"\\n--- RUNNING GA OPTIMIZER: SAFE (CONSERVATIVE) ---\")\n",
    "res_safe = optimize_portfolio_flow(capital, \"safe\", duration_years=3, mode=\"numpy_vectorized\")\n",
    "print(f\"Projected Return: {res_safe['return']['percentage']}\")\n",
    "print(f\"Volatility Level (Risk): {res_safe['volatility']['percentage']} ({res_safe['volatility']['label']})\")\n",
    "print(f\"Sharpe Ratio: {res_safe['sharpe']['value']} ({res_safe['sharpe']['label']})\")\n",
    "\n",
    "# 2. Aggressive Risk Profile (Max Stock allocation 80%)\n",
    "print(\"\\n--- RUNNING GA OPTIMIZER: AGGRESSIVE ---\")\n",
    "res_agg = optimize_portfolio_flow(capital, \"aggressive\", duration_years=3, mode=\"numpy_vectorized\")\n",
    "print(f\"Projected Return: {res_agg['return']['percentage']}\")\n",
    "print(f\"Volatility Level (Risk): {res_agg['volatility']['percentage']} ({res_agg['volatility']['label']})\")\n",
    "print(f\"Sharpe Ratio: {res_agg['sharpe']['value']} ({res_agg['sharpe']['label']})\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Capital Allocation Visualization (Pie Chart)\n",
    "Let's visualize where the IDR 10,000,000 capital should be deployed based on the **Safe (Conservative)** vs **Aggressive** recommendations."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "fig, axes = plt.subplots(1, 2, figsize=(16, 7))\n",
    "\n",
    "# Subplot 1: Safe\n",
    "safe_alloc = res_safe[\"allocation\"]\n",
    "safe_labels = [item[\"asset\"] for item in safe_alloc]\n",
    "safe_sizes = [float(item[\"percentage\"].replace(\"%\", \"\")) for item in safe_alloc]\n",
    "axes[0].pie(safe_sizes, labels=safe_labels, autopct='%1.1f%%', startangle=140, shadow=True)\n",
    "axes[0].set_title(\"Portfolio Recommendation: SAFE (IDR 10,000,000)\", fontsize=12, fontweight='bold')\n",
    "\n",
    "# Subplot 2: Aggressive\n",
    "agg_alloc = res_agg[\"allocation\"]\n",
    "agg_labels = [item[\"asset\"] for item in agg_alloc]\n",
    "agg_sizes = [float(item[\"percentage\"].replace(\"%\", \"\")) for item in agg_alloc]\n",
    "axes[1].pie(agg_sizes, labels=agg_labels, autopct='%1.1f%%', startangle=140, shadow=True)\n",
    "axes[1].set_title(\"Portfolio Recommendation: AGGRESSIVE (IDR 10,000,000)\", fontsize=12, fontweight='bold')\n",
    "\n",
    "plt.tight_layout()\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## 4. Parallel Computing Performance Benchmarking\n",
    "Core Academic Section: We compare 6 computational backends in evaluating Sharpe Ratios for 1,000 portfolio combinations, and verify the numeric consistency of the results."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "from backend.benchmark.runner import run_benchmark\n",
    "\n",
    "# 1. Setup benchmark matrices\n",
    "df_returns_dynamic = df_prices.pct_change().dropna()\n",
    "T_ret = len(df_returns_dynamic)\n",
    "deposito_daily_ret = bi_rate / 252.0\n",
    "sbn_daily_ret = sbn_rate / 252.0\n",
    "\n",
    "df_returns = pd.DataFrame(index=df_returns_dynamic.index)\n",
    "df_returns[\"DEPOSITO\"] = np.full(T_ret, deposito_daily_ret)\n",
    "df_returns[\"SBN ORI\"] = np.full(T_ret, sbn_daily_ret)\n",
    "for col in df_returns_dynamic.columns:\n",
    "    df_returns[col] = df_returns_dynamic[col]\n",
    "    \n",
    "asset_names = df_returns.columns.tolist()\n",
    "mu = df_returns.mean().values * 252.0\n",
    "mu[0] = bi_rate\n",
    "mu[1] = sbn_rate\n",
    "Sigma = np.cov(df_returns.values, rowvar=False) * 252.0\n",
    "\n",
    "P_rel = np.zeros((T_ret + 1, len(asset_names)))\n",
    "P_rel[0, :] = 1.0\n",
    "for t in range(1, T_ret + 1):\n",
    "    P_rel[t, 0] = (1.0 + deposito_daily_ret) ** t\n",
    "    P_rel[t, 1] = (1.0 + sbn_daily_ret) ** t\n",
    "for col_idx, col_name in enumerate(asset_names[2:], start=2):\n",
    "    initial_price = df_prices[col_name].iloc[0]\n",
    "    if initial_price > 0:\n",
    "        P_rel[:, col_idx] = df_prices[col_name].values[:T_ret+1] / initial_price\n",
    "    else:\n",
    "        P_rel[:, col_idx] = 1.0\n",
    "\n",
    "# 2. Run high-precision 6-method benchmark\n",
    "df_benchmark = run_benchmark(df_prices, mu, Sigma, P_rel, profile_name=\"balanced\")\n",
    "display(df_benchmark)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "### Execution Time & Speedup Comparison Plot\n",
    "Let's visualize the computation speedup of GPU & parallel CPU backends compared to Sequential Python using a bar chart."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "metadata": {},
   "outputs": [],
   "source": [
    "plt.figure(figsize=(12, 6))\n",
    "colors = ['#f87171', '#60a5fa', '#fbbf24', '#34d399', '#a78bfa', '#fb923c']\n",
    "\n",
    "# Bar chart of execution times\n",
    "bars = plt.bar(df_benchmark[\"Method\"], df_benchmark[\"Time (s)\"], color=colors[:len(df_benchmark)])\n",
    "plt.ylabel(\"Execution Time (Seconds)\", fontsize=11, fontweight='bold')\n",
    "plt.title(\"Computation Performance: Portfolio Evaluation Times (P=1,000)\", fontsize=13, fontweight='bold')\n",
    "plt.xticks(rotation=15)\n",
    "\n",
    "# Add numeric label on top of each bar\n",
    "for bar in bars:\n",
    "    yval = bar.get_height()\n",
    "    if not np.isnan(yval):\n",
    "        plt.text(bar.get_x() + bar.get_width()/2.0, yval + (max(df_benchmark[\"Time (s)\"])*0.01), f\"{yval:.4f} s\", ha='center', va='bottom', fontsize=9, fontweight='bold')\n",
    "\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "# Print resume speedup\n",
    "print(\"\\n=== ACCELERATION SPEEDUP RESUME ===\")\n",
    "for idx, row in df_benchmark.iterrows():\n",
    "    print(f\"{row['Method']}: {row['Time (s)']:.4f} s (Speedup: {row['Speedup']:.2f}x)\")"
   ]
  }
 ],
 "metadata": {
  "focus_cell": 0,
  "kernelspec": {
   "display_name": "spark311",
   "language": "python",
   "name": "spark311"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.11.15"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}

# Write notebook JSON file
notebook_path = "d:/INFORMATICS/SEMESTER 4/PARALLEL PROCESSING/Spark/OptiGene_Demo.ipynb"
with open(notebook_path, "w") as f:
    json.dump(notebook_content, f, indent=1)

print("Jupyter Notebook OptiGene_Demo.ipynb successfully generated!")
