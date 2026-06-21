def format_idr(val: float) -> str:
    return f"Rp {val:,.0f}".replace(",", ".")

def _clean_asset_name(name: str) -> str:
    name_upper = name.upper()
    if name_upper == "DEPOSITO":
        return "Deposito"
    elif "SBN" in name_upper or "ORI" in name_upper:
        return "Obligasi SBN"
    elif name_upper == "GOLD" or "EMAS" in name_upper:
        return "Emas (ANTM)"
    else:
        return name.replace(".JK", "").replace(".jk", "")

def format_layman_results(results: dict, capital: float, duration_years: int = 1) -> dict:
    """
    Converts technical portfolio optimization results into a layman-friendly format
    understandable by investment beginners in Indonesian.
    """
    weights = results["weights"]
    expected_return = results["return"]
    volatility = results["volatility"]
    sharpe = results["sharpe"]
    max_dd = results["max_drawdown"]
    
    # 1. Format Asset Allocation to IDR
    allocation_details = []
    
    # Category labels
    asset_names = results.get("asset_names", ["Deposito", "Obligasi SBN", "Emas (ANTM)"] + [f"Saham {i}" for i in range(len(weights)-3)])
    
    for name, weight in zip(asset_names, weights):
        if weight > 0.001:  # Display only if allocation > 0.1%
            allocated_money = capital * weight
            clean_name = _clean_asset_name(name)
            allocation_details.append({
                "asset": clean_name,
                "percentage": f"{weight * 100:.2f}%",
                "nominal": format_idr(allocated_money),
                "description": _get_asset_description(name)
            })
            
    # 2. Format Returns
    annual_profit = capital * expected_return
    # Calculate compounded returns
    compounded_value = capital * ((1 + expected_return) ** duration_years)
    compounded_profit = compounded_value - capital
    
    layman_return = {
        "percentage": f"{expected_return * 100:.2f}% per tahun",
        "description": f"Modal Anda sebesar {format_idr(capital)} diproyeksikan tumbuh menjadi {format_idr(compounded_value)} dalam {duration_years} tahun (akumulasi keuntungan sebesar {format_idr(compounded_profit)}).",
        "summary": f"Estimasi profit: +{format_idr(annual_profit)}/tahun"
    }
    
    # 3. Format Risk (Volatility)
    if volatility < 0.05:
        vol_label = "Sangat Rendah (Aman)"
        vol_desc = "Fluktuasi harga sangat kecil. Sangat stabil, mirip dengan tabungan biasa."
    elif volatility < 0.10:
        vol_label = "Rendah (Stabil)"
        vol_desc = "Fluktuasi harga kecil. Cocok untuk investor yang menginginkan pertumbuhan stabil tanpa penurunan nilai yang mendadak."
    elif volatility < 0.18:
        vol_label = "Sedang (Moderat)"
        vol_desc = "Fluktuasi harga normal. Mengalami pergerakan jangka pendek yang moderat namun relatif aman dalam jangka menengah."
    else:
        vol_label = "Tinggi (Agresif)"
        vol_desc = "Harga berfluktuasi cepat. Potensi keuntungan tinggi, namun membutuhkan kesiapan mental menghadapi penurunan pasar."
        
    layman_volatility = {
        "label": vol_label,
        "percentage": f"{volatility * 100:.2f}%",
        "description": vol_desc
    }
    
    # 4. Format Worst-Case Loss (Max Drawdown)
    potential_loss = capital * max_dd
    layman_drawdown = {
        "percentage": f"{max_dd * 100:.2f}%",
        "nominal": format_idr(potential_loss),
        "description": f"Dalam skenario terburuk pasar secara historis (seperti krisis keuangan), portofolio ini mengalami penurunan sementara maksimum sebesar {max_dd * 100:.1f}%, atau setara dengan {format_idr(potential_loss)}. Penurunan ini bersifat sementara sebelum nilainya kembali pulih."
    }
    
    # 5. Format Portfolio Efficiency (Sharpe Ratio)
    if sharpe < 0.5:
        sharpe_label = "Efisiensi Rendah"
        sharpe_desc = "Potensi keuntungan yang diharapkan kurang sebanding dengan tingkat risiko yang diambil."
    elif sharpe < 1.2:
        sharpe_label = "Keseimbangan Cukup"
        sharpe_desc = "Kombinasi portofolio seimbang di mana return sebanding dengan tingkat volatilitas."
    elif sharpe < 2.0:
        sharpe_label = "Efisiensi Tinggi"
        sharpe_desc = "Sangat efisien! Algoritma menemukan kombinasi optimal yang memaksimalkan return dengan volatilitas rendah."
    else:
        sharpe_label = "Sangat Optimal"
        sharpe_desc = "Desain portofolio luar biasa! Keuntungan maksimal dicapai dengan risiko keseluruhan yang sangat terkendali."
        
    layman_sharpe = {
        "value": f"{sharpe:.2f}",
        "label": sharpe_label,
        "description": sharpe_desc
    }
    
    # 6. Format GA Insight
    layman_ga = {
        "insight": "Sistem kami mensimulasikan dan mengevaluasi lebih dari 100.000 kombinasi portofolio melalui 500 generasi optimasi Algoritma Genetika untuk menemukan alokasi terbaik di atas."
    }
    
    return {
        "capital": format_idr(capital),
        "duration_years": duration_years,
        "allocation": allocation_details,
        "return": layman_return,
        "volatility": layman_volatility,
        "drawdown": layman_drawdown,
        "sharpe": layman_sharpe,
        "ga_insight": layman_ga
    }

def _get_asset_description(name: str) -> str:
    """
    Layman-friendly description for types of assets in Indonesian.
    """
    name_upper = name.upper()
    if "DEPOSITO" in name_upper or "TIME DEPOSIT" in name_upper:
        return "Tabungan jangka pendek bunga tetap dijamin LPS. Sangat aman."
    elif "SBN" in name_upper or "ORI" in name_upper or "BOND" in name_upper:
        return "Surat Berharga Negara. Dijamin 100% oleh Pemerintah RI."
    elif "EMAS" in name_upper or "ANTM" in name_upper or "GC=F" in name_upper or "GOLD" in name_upper:
        return "Emas Fisik (ANTM). Pelindung nilai terbaik dari inflasi & krisis."
    else:
        # Stock
        ticker = name.replace(".JK", "").replace(".jk", "")
        return f"Saham perusahaan terbuka ({ticker}). Potensi profit tinggi dari ekuitas bisnis."

