import numpy as np

RISK_PROFILES = {
    "aman": {
        "max_saham": 0.20,       # Maks 20% di saham/emas
        "min_fixed": 0.60,       # Min 60% di deposito/SBN
        "max_drawdown": 0.05,    # Maks drawdown 5%
    },
    "seimbang": {
        "max_saham": 0.50,
        "min_fixed": 0.30,
        "max_drawdown": 0.15,
    },
    "agresif": {
        "max_saham": 0.80,
        "min_fixed": 0.10,
        "max_drawdown": 0.30,
    }
}

def get_constraints(profile: str) -> dict:
    """
    Mengambil konfigurasi batasan berdasarkan profil risiko.
    """
    p_clean = profile.lower().strip()
    return RISK_PROFILES.get(p_clean, RISK_PROFILES["seimbang"])

def project_weights(w: np.ndarray) -> np.ndarray:
    """
    Memproyeksikan bobot portofolio agar:
    1. Semua bobot bernilai non-negatif (>= 0).
    2. Jumlah total bobot sama dengan 1.0.
    """
    # 1. Pastikan non-negatif
    w_clip = np.clip(w, 0.0, None)
    
    # 2. Normalisasi agar sum = 1.0
    s = np.sum(w_clip)
    if s > 0:
        return w_clip / s
    else:
        # Jika semua nol, bagi rata
        n = len(w)
        return np.ones(n) / n

def validate_portfolio_constraints(w: np.ndarray, profile_name: str) -> bool:
    """
    Validasi cepat apakah bobot portofolio memenuhi batas kategori profil risiko.
    Indeks 0 = Deposito, Indeks 1 = SBN (Fixed Income).
    Indeks 2 dst = Saham & Emas (Dynamic/Saham).
    """
    cons = get_constraints(profile_name)
    
    fixed_weight = w[0] + w[1]
    saham_weight = np.sum(w[2:])
    
    if saham_weight > cons["max_saham"]:
        return False
    if fixed_weight < cons["min_fixed"]:
        return False
        
    return True
