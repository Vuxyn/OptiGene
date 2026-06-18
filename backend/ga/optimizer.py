import numpy as np
import logging
from backend.ga.constraints import project_weights, get_constraints
from backend.ga.fitness import evaluate_population

logger = logging.getLogger(__name__)

def repair_portfolio_weights(w: np.ndarray, profile_name: str) -> np.ndarray:
    """
    Fungsi perbaikan konstruktif untuk memaksa bobot portofolio mematuhi
    batasan alokasi kategori saham/fixed income sesuai profil risiko.
    """
    w = project_weights(w)
    cons = get_constraints(profile_name)
    
    fixed_idx = [0, 1]              # Deposito, SBN
    saham_idx = list(range(2, len(w))) # Saham, Emas
    
    fixed_sum = w[0] + w[1]
    saham_sum = np.sum(w[2:])
    
    max_saham = cons["max_saham"]
    min_fixed = cons["min_fixed"]
    
    # 1. Batasi bobot saham maksimal
    if saham_sum > max_saham:
        if saham_sum > 0:
            w[saham_idx] = w[saham_idx] * (max_saham / saham_sum)
        else:
            w[saham_idx] = 0.0
            
        fixed_target = 1.0 - max_saham
        if fixed_sum > 0:
            w[fixed_idx] = w[fixed_idx] * (fixed_target / fixed_sum)
        else:
            w[fixed_idx] = np.array([0.5, 0.5]) * fixed_target
            
    # Hitung ulang sum saat ini
    fixed_sum = w[0] + w[1]
    saham_sum = np.sum(w[2:])
    
    # 2. Batasi bobot fixed income minimal
    if fixed_sum < min_fixed:
        if fixed_sum > 0:
            w[fixed_idx] = w[fixed_idx] * (min_fixed / fixed_sum)
        else:
            w[fixed_idx] = np.array([0.5, 0.5]) * min_fixed
            
        saham_target = 1.0 - min_fixed
        if saham_sum > 0:
            w[saham_idx] = w[saham_idx] * (saham_target / saham_sum)
        else:
            w[saham_idx] = 0.0
            
    return project_weights(w)

class GeneticOptimizer:
    def __init__(
        self, 
        pop_size: int = 1000, 
        generations: int = 500, 
        crossover_rate: float = 0.8, 
        mutation_rate: float = 0.1, 
        elitism_count: int = 10
    ):
        self.pop_size = pop_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elitism_count = elitism_count

    def run(
        self, 
        mu: np.ndarray, 
        Sigma: np.ndarray, 
        P_rel: np.ndarray, 
        profile_name: str, 
        mode: str = "numpy_vectorized",
        spark = None
    ) -> dict:
        """
        Menjalankan alur optimasi Genetic Algorithm untuk mencari alokasi bobot optimal.
        """
        N = len(mu)
        cons = get_constraints(profile_name)
        
        # Menggunakan BI Rate (index 0) sebagai suku bunga bebas risiko (risk-free rate)
        # di Sharpe Ratio. Jika nilainya nol, kita gunakan 0.05 sebagai standard.
        rf_rate = mu[0] if mu[0] > 0 else 0.05
        
        # 1. Inisialisasi Populasi secara acak dan langsung di-repair
        population = np.random.rand(self.pop_size, N)
        for i in range(self.pop_size):
            population[i] = repair_portfolio_weights(population[i], profile_name)
            
        best_sharpe_history = []
        best_portfolio = None
        best_w = None
        best_ret = 0.0
        best_vol = 0.0
        best_dd = 0.0
        
        logger.info(f"Memulai GA dengan backend '{mode}' untuk profil '{profile_name}'...")
        
        for gen in range(self.generations):
            # 2. Evaluasi populasi (hitung Return, Vol, Sharpe)
            # Sharpe disembunyikan jika melebihi batas drawdown dalam evaluasi
            rets, vols, sharpes = evaluate_population(population, mu, Sigma, rf_rate, mode, spark)
            
            # 3. Hitung Max Drawdown untuk penalti constraint dinamis
            # Untuk mempercepat GA, kita hitung drawdown hanya untuk individu-individu top 
            # atau jika dihitung per individu saat evaluasi. Di fitness.py, kita hitung sharpe.
            # Kita bisa memvalidasi max_drawdown di sini.
            # Karena menghitung drawdown membutuhkan matriks P_rel yang besar, 
            # kita lakukan kalkulasi drawdown secara efisien di CPU NumPy untuk populasi saat ini.
            # Nilai portofolio historis: P x T
            port_values = np.dot(population, P_rel.T) # (P, N) x (N, T) -> (P, T)
            
            # Cari cumulative max sepanjang baris (hari) untuk tiap portfolio
            cum_maxes = np.maximum.accumulate(port_values, axis=1)
            drawdowns = (cum_maxes - port_values) / cum_maxes
            max_dds = np.max(drawdowns, axis=1)
            
            # Berikan penalti berat ke Sharpe Ratio jika melanggar batas max_drawdown profil risiko
            violators = max_dds > cons["max_drawdown"]
            sharpes = np.where(violators, -99.0, sharpes)
            
            # 4. Cari portofolio terbaik di generasi ini
            best_idx = np.argmax(sharpes)
            current_best_sharpe = sharpes[best_idx]
            
            if best_portfolio is None or current_best_sharpe > best_portfolio:
                best_portfolio = current_best_sharpe
                best_w = population[best_idx].copy()
                best_ret = rets[best_idx]
                best_vol = vols[best_idx]
                best_dd = max_dds[best_idx]
                
            best_sharpe_history.append(float(best_portfolio))
            
            if (gen + 1) % 100 == 0 or gen == 0:
                logger.info(f"Generasi {gen+1}/{self.generations} | Best Sharpe: {best_portfolio:.4f} | Return: {best_ret*100:.2f}% | Vol: {best_vol*100:.2f}% | Max DD: {best_dd*100:.2f}%")
                
            # 5. Seleksi Elitisme (ambil top M individu terbaik)
            elite_indices = np.argsort(sharpes)[-self.elitism_count:]
            new_population = np.zeros_like(population)
            new_population[:self.elitism_count] = population[elite_indices]
            
            # 6. Bentuk populasi baru (Crossover & Mutasi)
            idx_new = self.elitism_count
            while idx_new < self.pop_size:
                # Tournament Selection (k=3)
                p1_idx = self._tournament_selection(sharpes, k=3)
                p2_idx = self._tournament_selection(sharpes, k=3)
                p1 = population[p1_idx]
                p2 = population[p2_idx]
                
                # Crossover
                if np.random.rand() < self.crossover_rate:
                    alpha = np.random.rand(N)
                    c1 = alpha * p1 + (1.0 - alpha) * p2
                    c2 = (1.0 - alpha) * p1 + alpha * p2
                else:
                    c1, c2 = p1.copy(), p2.copy()
                    
                # Mutation
                if np.random.rand() < self.mutation_rate:
                    c1 = self._mutate(c1)
                if np.random.rand() < self.mutation_rate:
                    c2 = self._mutate(c2)
                    
                # Repair batasan alokasi
                new_population[idx_new] = repair_portfolio_weights(c1, profile_name)
                if idx_new + 1 < self.pop_size:
                    new_population[idx_new + 1] = repair_portfolio_weights(c2, profile_name)
                    
                idx_new += 2
                
            population = new_population
            
        logger.info(f"GA Selesai. Sharpe Optimal: {best_portfolio:.4f}")
        return {
            "weights": best_w.tolist(),
            "return": float(best_ret),
            "volatility": float(best_vol),
            "sharpe": float(best_portfolio),
            "max_drawdown": float(best_dd),
            "history": best_sharpe_history
        }

    def _tournament_selection(self, sharpes: np.ndarray, k: int = 3) -> int:
        candidates = np.random.choice(len(sharpes), size=k, replace=False)
        best_candidate = candidates[np.argmax(sharpes[candidates])]
        return best_candidate

    def _mutate(self, w: np.ndarray) -> np.ndarray:
        # Tambahkan noise gaussian kecil ke salah satu bobot secara acak
        N = len(w)
        mutate_idx = np.random.randint(0, N)
        w[mutate_idx] += np.random.normal(0, 0.05)
        return w
