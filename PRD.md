# Product Requirements Document (PRD)
## Portfolio Optimizer — Parallel Computing Project
**Version:** 1.0 | **Date:** June 2026

---

## 1. Overview

### Problem Statement
Average retail investors struggle to allocate capital to suitable investment assets (time deposits, government bonds, stocks, gold). Most existing portfolio optimization tools are too mathematical or technical, preventing standard users from utilizing them effectively.

### Solution
An interactive multi-asset portfolio optimization web application using a Genetic Algorithm (GA) accelerated by parallel computing architectures (PySpark & CUDA), displaying layman-friendly outputs.

### Academic Goal
Empirically demonstrate that parallel computing frameworks are significantly faster than sequential execution for evaluating massive portfolio options while yielding identical numerical results.

---

## 2. Target Users

| User Category | Needs & Use Cases |
|---|---|
| Students / Researchers | Inspect execution time comparisons across Sequential vs. PySpark vs. CUDA GPU |
| Retail Investors | Quick answers to: "Where should I invest my IDR 5 million capital?" |
| Evaluators / Professors | Technical proof of integrated GA + PySpark + CUDA code functionality |

---

## 3. Scoring Criteria

| Component | Weight |
|---|---|
| PySpark operations (SQL, map, reduce, filter) | Base score |
| High-precision execution time benchmark | Mandatory |
| CUDA with explicit grid and thread dimensions | +20 bonus points |
| 5-minute explanation video | Mandatory |
| **Maximum Score** | **170 points** |

---

## 4. Data Layer

### Data Sources (Dynamic Fetching)
- **IDX Stocks:** `yfinance` (suffix `.JK`)
- **Gold:** `yfinance` (`ANTM.JK` or global ticker `GC=F` as fallback)
- **Time Deposits:** Web scraping the BI Rate from Bank Indonesia
- **Government Bonds (SBN):** Web scraping indices from DJPPR/CNBC Indonesia

### Asset Universe
- **Stocks:** LQ45 index constituents (~25 stable stocks with sufficient listing history)
- **Fixed Income:** BI-rate Time Deposits, 10-Year SBN ORI Government Bonds
- **Commodities:** Gold Bullion

### Data Validation & Filters
- Exclude stocks listed for less than 3 years (avoid survivorship bias)
- Exclude stocks with data coverage < 95%
- Time period: 2022-01-01 to 2024-12-31 (3 years post-COVID stabilization)
- Automate clean fills (forward and backward fill) for holiday gaps

---

## 5. System Architecture

```
                 USER INPUT
        (Capital, Risk Profile, Duration)
                     │
                     ▼
                 DATA LAYER
      (yfinance + BI Scraping + DJPPR Cache)
                     │
                     ▼
               PYSPARK ENGINE
      (ETL + SQL + map + reduce + filter)
                     │
                     ▼
             BENCHMARK RUNNER
    (Sequential vs. Spark vs. CUDA vs. Hybrid)
                     │
                     ▼
                GA OPTIMIZER
     (Population, Cross, Mutate, Elite)
         (Fitness evaluated via GPU/CPU)
                     │
                     ▼
              FASTAPI BACKEND
        (Formats metrics to layman terms)
                     │
                     ▼
              FRONTEND WEB UI
     (Next.js Dashboard + Charts.js)
```

---

## 6. Technical Components

### 6.1 PySpark Parallelization (Required)

| Operation | Implementation & Purpose |
|---|---|
| SparkSession SQL | Querying mean historical returns and standard deviation |
| RDD map | Computing Sharpe Ratio and risk boundaries for each portfolio candidate |
| RDD filter | Pruning portfolios violating user risk boundaries |
| RDD reduce | Finding the absolute highest Sharpe Ratio portfolio from the population |

### 6.2 CUDA Acceleration (Bonus +20)

| Kernel function | Description |
|---|---|
| `covariance_kernel` | Computing asset return covariances in a 2D grid block |
| `evaluate_portfolios_kernel` | Evaluating Sharpe ratios for the entire 1,000+ population in parallel |
| `monte_carlo_simulation_kernel` | Simulating asset growth paths for future projections |

Thread and grid configuration must be explicitly set:
```c
int blocks  = (n_portfolios + 255) / 256;
int threads = 256;
kernel<<<blocks, threads>>>(args);
```

### 6.3 Genetic Algorithm Configuration

| Property | Setting / Methodology |
|---|---|
| Individual | Vector of weights summing up to 1.0 |
| Population Size | 1000 portfolios |
| Generations | 500 generations |
| Fitness Score | Sharpe Ratio (computed on CPU or GPU backend) |
| Crossover | Vector arithmetic blend |
| Mutation | Gaussian noise random shifting |
| Constraints | Risk profiles, minimum allocation boundary, maximum allocation boundary |

### 6.4 PySpark + CUDA Hybrid Approach

```
PySpark partition weights list
              ↓
Each Partition → evaluates using CuPy on GPU worker nodes
              ↓
Collect & reduce outputs back to driver node
```

*Note:* PySpark + CUDA hybrid has some overhead on communication but scales best for massive distributed datasets.

---

## 7. High-Precision Benchmarking

Benchmark operation: Sharpe Ratio evaluation for **1000 portfolios** under identical mathematical requirements.

| Method ID | Method Name | Execution Time Expectation | Speedup |
|---|---|---|---|
| 1 | Sequential Python (For Loop) | ~45 seconds | 1.0x (Baseline) |
| 2 | PySpark SQL Query | ~8 seconds | ~5.6x |
| 3 | PySpark RDD map | ~5 seconds | ~8.7x |
| 4 | PySpark RDD filter + reduce | ~4.8 seconds | ~9.4x |
| 5 | Pure CUDA (GPU) | ~0.3 seconds | ~150.0x |
| 6 | PySpark + CUDA Hybrid | ~1.5 seconds | ~30.0x |

**Verification Rule: Best Sharpe values and return outputs must match exactly across all backends! ✅**

---

## 8. User Experience & Translation

### User Inputs
- Investment Capital (IDR)
- Risk Profile: Conservative (Safe) / Moderate (Balanced) / Aggressive
- Jangka Waktu (Duration): 1 Year / 3 Years / 5 Years

### Output Formatting (Layman Terms)

| Technical Representation | Layman Conversion |
|---|---|
| Asset Weight: 0.40 | "Invest IDR 2,000,000 in Time Deposits" |
| Expected Return: 8.3% | "Estimated profit: +IDR 415,000 / year (IDR 6,400,000 total in 3 years)" |
| Max Drawdown: 6% | "Worst-case historical temporary drop: IDR 300,000" |
| GA 500 Generations | "Simulated over 100,000 portfolio combinations" |
| Sharpe Ratio | "How worth it the return is compared to the risk" |
| Volatility | "How much the price fluctuates up and down" |

---

## 9. Monorepo Structure

```
portfolio-optimizer/
├── frontend/             # Next.js SPA Web App
│   ├── app/              # Router, layouts, styles, and page component
│   └── package.json
├── backend/              # FastAPI Python Web API
│   ├── app.py            # API controller & Uvicorn router
│   ├── orchestrator.py   # Flow controller
│   ├── formatter.py      # Technical-to-layman translation
│   ├── data/             # fetcher, validator, cache
│   ├── pyspark/          # session, context
│   ├── cuda/             # kernels, fallback
│   ├── ga/               # optimizer, fitness, constraints
│   └── benchmark/        # runner.py
└── results/              # Output CSV and config logs
```

---

## 10. Verification Metric Targets

| Metric | Target |
|---|---|
| Output Consistency | Sharpe differences across methods < $10^{-4}$ |
| PySpark CPU Speedup | $\ge$ 3x speedup vs. sequential |
| CUDA GPU Speedup | $\ge$ 50x speedup vs. sequential |
| Convergence | Sharpe increase across generations |
| Data Reliability | Coverage $\ge$ 95% over the 2022-2024 timeframe |
| UX Simplicity | Full run takes less than 1 minute |
