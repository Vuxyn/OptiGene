import numpy as np

RISK_PROFILES = {
    "aman": {
        "max_saham": 0.20,       # Max 20% in stocks/gold
        "min_fixed": 0.60,       # Min 60% in deposits/SBN
        "max_drawdown": 0.05,    # Max drawdown 5%
    },
    "safe": {
        "max_saham": 0.20,
        "min_fixed": 0.60,
        "max_drawdown": 0.05,
    },
    "conservative": {
        "max_saham": 0.20,
        "min_fixed": 0.60,
        "max_drawdown": 0.05,
    },
    "seimbang": {
        "max_saham": 0.50,
        "min_fixed": 0.30,
        "max_drawdown": 0.15,
    },
    "balanced": {
        "max_saham": 0.50,
        "min_fixed": 0.30,
        "max_drawdown": 0.15,
    },
    "moderate": {
        "max_saham": 0.50,
        "min_fixed": 0.30,
        "max_drawdown": 0.15,
    },
    "agresif": {
        "max_saham": 0.80,
        "min_fixed": 0.10,
        "max_drawdown": 0.30,
    },
    "aggressive": {
        "max_saham": 0.80,
        "min_fixed": 0.10,
        "max_drawdown": 0.30,
    }
}

def get_constraints(profile: str) -> dict:
    """
    Retrieves the constraint configuration based on the risk profile.
    """
    p_clean = profile.lower().strip()
    return RISK_PROFILES.get(p_clean, RISK_PROFILES["seimbang"])

def project_weights(w: np.ndarray) -> np.ndarray:
    """
    Projects the portfolio weights such that:
    1. All weights are non-negative (>= 0).
    2. The sum of all weights equals 1.0.
    """
    # 1. Ensure non-negativity
    w_clip = np.clip(w, 0.0, None)
    
    # 2. Normalize to sum = 1.0
    s = np.sum(w_clip)
    if s > 0:
        return w_clip / s
    else:
        # If all are zero, distribute equally
        n = len(w)
        return np.ones(n) / n

def validate_portfolio_constraints(w: np.ndarray, profile_name: str) -> bool:
    """
    Quickly validates if the portfolio weights satisfy the boundaries of the risk profile.
    Index 0 = Time Deposit, Index 1 = Government Bonds (SBN) (Fixed Income).
    Index 2 and onwards = Stocks & Gold (Dynamic / Stocks).
    """
    cons = get_constraints(profile_name)
    
    fixed_weight = w[0] + w[1]
    saham_weight = np.sum(w[2:])
    
    if saham_weight > cons["max_saham"]:
        return False
    if fixed_weight < cons["min_fixed"]:
        return False
        
    return True
