# AGENT CONTEXT — Portfolio Optimizer Project

## Project Identity
You are the coding assistant for the **Portfolio Optimizer** project, an application that helps retail investors allocate capital to the best investment instruments using a Genetic Algorithm (GA) accelerated with PySpark and CUDA.

---

## Project Objectives
1. **Academic:** Empirically prove that parallel computing (PySpark & CUDA) is faster than sequential execution for portfolio evaluation while yielding identical results.
2. **End User:** Help retail investors answer the question "I have IDR 5 million, where should I put it?" with easy-to-understand allocation recommendations.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Data Fetching | `yfinance`, `requests`, `BeautifulSoup` |
| Data Processing | PySpark (SparkSession + SparkContext RDD) |
| GPU Computing | CUDA C / CuPy |
| Optimizer | Genetic Algorithm (Python) |
| Backend | FastAPI (Python + Uvicorn) |
| Frontend | Next.js + Tailwind CSS + Chart.js |

---

## Development Guidelines

### PySpark — MUST use these 4 approaches:
```python
# 1. SparkSession SQL Query
spark.sql("SELECT ...")

# 2. RDD map
rdd.map(lambda x: ...)

# 3. RDD filter
rdd.filter(lambda x: ...)

# 4. RDD reduce
rdd.reduce(lambda a, b: ...)
```
Every approach MUST have its execution time measured and compared.

### CUDA — MUST use explicit grid & thread dimensions:
```c
int blocks  = (n + 255) / 256;
int threads = 256;
kernel<<<blocks, threads>>>(args);
```
Required kernels: `covarianceMatrix`, `evaluateAllPortfolios`.

### Genetic Algorithm:
- Individual = array of allocation weights per asset (sum = 1.0)
- Fitness = Sharpe Ratio
- Population = 1000, Generations = 500
- Fitness evaluation function is accelerated via CUDA / PySpark / hybrid

### Benchmark Runner — MUST include 6 execution methods:
```
1. Sequential Python    → baseline
2. PySpark SQL          → parallel CPU
3. PySpark RDD map      → parallel CPU
4. PySpark filter+reduce→ parallel CPU
5. Pure CUDA            → parallel GPU
6. PySpark + CUDA       → hybrid (scalable)
```
The operations being compared MUST be identical (Sharpe Ratio evaluation for 1000 portfolios).

---

## Optimized Assets

```python
ASSET_UNIVERSE = {
    "fixed": [
        {"name": "Time Deposit", "source": "bi_rate"},
        {"name": "Government Bonds (SBN)", "source": "djppr_api"},
    ],
    "dynamic": [
        {"name": "IDX Stock", "source": "yfinance", "index": "LQ45"},
        {"name": "Gold", "source": "yfinance", "ticker": "ANTM.JK"},
    ]
}
```

### Data Validation — REQUIRED:
- Only stocks with listing history > 3 years
- Data coverage $\ge$ 95%
- Period: 2022-01-01 to 2024-12-31 (post-COVID)
- Auto-reject stocks with incomplete data

---

## Output Format for End Users

Always convert technical outputs to layman-friendly descriptions:

| Don't Use (Technical) | Use Instead (Layman-friendly) |
|---|---|
| `weight: 0.40` | "Invest IDR 2 million in Time Deposits" |
| `return: 8.3%` | "Estimated growth in 3 years to IDR 6.4 million" |
| `max_drawdown: 6%` | "Under worst-case scenarios, temporary dip could reach IDR 300K" |
| `500 GA generations` | "The computer simulated 100,000 portfolio combinations" |
| `Sharpe Ratio` | "How efficient the return is compared to the risk" |
| `volatility` | "How much the price fluctuates up and down" |

---

## GA Constraints based on Risk Profile

```python
RISK_PROFILES = {
    "safe": {
        "max_saham"   : 0.20,   # max 20% in stocks/gold
        "min_fixed"   : 0.60,   # min 60% in deposits/bonds
        "max_drawdown": 0.05,
    },
    "balanced": {
        "max_saham"   : 0.50,
        "min_fixed"   : 0.30,
        "max_drawdown": 0.15,
    },
    "aggressive": {
        "max_saham"   : 0.80,
        "min_fixed"   : 0.10,
        "max_drawdown": 0.30,
    }
}
```

---

## Execution Time Expectations

```
Sequential Python     : ~45 seconds (1x - baseline)
PySpark SQL           : ~8 seconds  (~5.6x speedup)
PySpark RDD map       : ~5 seconds  (~8.7x speedup)
PySpark filter+reduce : ~4.8 seconds (~9.4x speedup)
Pure CUDA             : ~0.3 seconds (~150x speedup)
PySpark + CUDA        : ~1.5 seconds (~30x speedup)
```

These values are estimates — actual results are stored in `results/benchmark.csv`.

---

## Crucial Implementation Details

1. **No Hardcoded Data** — fetch all rates and stock data dynamically from web resources / yfinance.
2. **PySpark + CUDA hybrid** is not necessarily the fastest for small datasets due to Spark broadcast overhead, but is the most scalable for massive datasets. Explain this in the final walkthrough.
3. **Walk-forward validation** — validate the GA across different sub-periods.
4. **Survivorship bias** — exclude any stock that was listed after the starting period (listing history < 3 years).

---

## Checklist Before Submission

- [ ] PySpark: SQL query, map, reduce, filter are all implemented
- [ ] Execution times of all 6 methods are recorded
- [ ] CUDA kernel written with explicit grid & thread dimensions
- [ ] GA converges (Sharpe Ratio increases across generations)
- [ ] Historical prices are validated (coverage $\ge$ 95%)
- [ ] UI is fully functional and uses non-technical layman formatting
- [ ] Verification video is prepared
