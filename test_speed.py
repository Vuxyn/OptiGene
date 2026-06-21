import time, sys
sys.path.insert(0, '.')
import numpy as np
import pandas as pd

print("=" * 50)
print("OptiGene GA Speed Test")
print("=" * 50)

t0 = time.time()
from backend.data.cache import load_prices_cache, load_rates_cache

rates = load_rates_cache()
df_prices = load_prices_cache()
print(f"[{time.time()-t0:.2f}s] Cache loaded | prices shape: {df_prices.shape}")

# Build returns
df_returns_dynamic = df_prices.pct_change().dropna()
T = len(df_returns_dynamic)
bi_rate = rates['bi_rate']
sbn_rate = rates['sbn_rate']

df_returns = pd.DataFrame(index=df_returns_dynamic.index)
df_returns['DEPOSITO'] = np.full(T, bi_rate / 252)
df_returns['SBN ORI']  = np.full(T, sbn_rate / 252)
for col in df_returns_dynamic.columns:
    df_returns[col] = df_returns_dynamic[col]

asset_names = df_returns.columns.tolist()
N = len(asset_names)
mu = df_returns.mean().values * 252
mu[0] = bi_rate
mu[1] = sbn_rate
Sigma = np.cov(df_returns.values, rowvar=False) * 252
Sigma = np.nan_to_num(Sigma)
print(f"[{time.time()-t0:.2f}s] Stats built | N assets: {N}")

# Build P_rel
P_rel = np.zeros((T + 1, N))
P_rel[0, :] = 1.0
for t in range(1, T + 1):
    P_rel[t, 0] = (1 + bi_rate  / 252) ** t
    P_rel[t, 1] = (1 + sbn_rate / 252) ** t
for ci, cn in enumerate(asset_names[2:], 2):
    ip = df_prices[cn].iloc[0]
    if ip > 0:
        P_rel[:, ci] = df_prices[cn].values[:T + 1] / ip
print(f"[{time.time()-t0:.2f}s] P_rel built")

# Run GA
from backend.ga.optimizer import GeneticOptimizer
opt = GeneticOptimizer(pop_size=500, generations=150)
t1 = time.time()
print(f"\nRunning GA (pop=500, gen=150) ...")
res = opt.run(mu, Sigma, P_rel, 'aman', mode='numpy_vectorized')
print(f"\n[DONE] GA time: {time.time()-t1:.2f}s | Total: {time.time()-t0:.2f}s")
print(f"Sharpe: {res['sharpe']:.4f} | Return: {res['return']*100:.2f}% | Vol: {res['volatility']*100:.2f}%")
