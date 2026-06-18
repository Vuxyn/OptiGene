def format_layman_results(results: dict, capital: float, duration_years: int = 1) -> dict:
    """
    Mengonversi hasil optimasi portofolio teknis ke dalam format bahasa awam
    yang mudah dipahami oleh pemula investasi.
    """
    weights = results["weights"]
    expected_return = results["return"]
    volatility = results["volatility"]
    sharpe = results["sharpe"]
    max_dd = results["max_drawdown"]
    
    # 1. Format Alokasi Aset ke Rupiah
    # Kami mengasumsikan urutan aset:
    # 0: Deposito, 1: SBN ORI, 2: Emas, 3 dst: Saham
    # Mari kita format list alokasi
    allocation_details = []
    
    # Kategori label
    # Ticker aset akan dipetakan dari modul orchestrator, di sini kita terima list bobot yang sesuai dengan nama aset
    asset_names = results.get("asset_names", ["Deposito", "SBN ORI", "Emas (ANTM)"] + [f"Saham {i}" for i in range(len(weights)-3)])
    
    for name, weight in zip(asset_names, weights):
        if weight > 0.001:  # Tampilkan hanya jika alokasi > 0.1%
            allocated_money = capital * weight
            allocation_details.append({
                "asset": name,
                "percentage": f"{weight * 100:.2f}%",
                "nominal": f"Rp {allocated_money:,.0f}".replace(",", "."),
                "description": _get_asset_description(name)
            })
            
    # 2. Format Keuntungan (Return)
    annual_profit = capital * expected_return
    future_value = capital + annual_profit
    # Menghitung compounding sederhana untuk jangka waktu tertentu
    compounded_value = capital * ((1 + expected_return) ** duration_years)
    compounded_profit = compounded_value - capital
    
    layman_return = {
        "percentage": f"{expected_return * 100:.2f}% per tahun",
        "description": f"Uang Anda sebesar Rp {capital:,.0f}.000 diproyeksikan bertumbuh menjadi Rp {compounded_value:,.0f}.000 dalam {duration_years} tahun (keuntungan Rp {compounded_profit:,.0f}.000)".replace(",", "."),
        "summary": f"Estimasi keuntungan: +Rp {annual_profit:,.0f}/tahun".replace(",", ".")
    }
    
    # 3. Format Risiko (Volatilitas)
    if volatility < 0.05:
        vol_label = "Sangat Rendah (Aman)"
        vol_desc = "Tingkat naik-turun harga sangat kecil. Sangat stabil seperti tabungan biasa."
    elif volatility < 0.10:
        vol_label = "Rendah (Stabil)"
        vol_desc = "Fluktuasi harga kecil. Cocok untuk Anda yang tidak ingin terkejut dengan penurunan nilai investasi."
    elif volatility < 0.18:
        vol_label = "Sedang (Moderat)"
        vol_desc = "Fluktuasi harga wajar. Ada potensi naik-turun harian namun cenderung aman dalam jangka menengah."
    else:
        vol_label = "Tinggi (Agresif)"
        vol_desc = "Harga naik-turun dengan cepat. Potensi keuntungan besar, namun siap-siap mental dengan pergerakan harga."
        
    layman_volatility = {
        "label": vol_label,
        "percentage": f"{volatility * 100:.2f}%",
        "description": vol_desc
    }
    
    # 4. Format Risiko Penurunan Terburuk (Max Drawdown)
    potential_loss = capital * max_dd
    layman_drawdown = {
        "percentage": f"{max_dd * 100:.2f}%",
        "nominal": f"Rp {potential_loss:,.0f}".replace(",", "."),
        "description": f"Dalam skenario pasar terburuk (seperti krisis), portofolio Anda pernah mengalami penurunan nilai maksimal sekitar {max_dd * 100:.1f}% atau setara Rp {potential_loss:,.0f}. Namun, ini adalah penurunan sementara sebelum harga pulih kembali.".replace(",", ".")
    }
    
    # 5. Format Kelayakan Portofolio (Sharpe Ratio)
    if sharpe < 0.5:
        sharpe_label = "Kurang Efisien"
        sharpe_desc = "Keuntungan yang didapat kurang sebanding dengan risiko yang Anda ambil."
    elif sharpe < 1.2:
        sharpe_label = "Cukup Sepadan"
        sharpe_desc = "Kombinasi portofolio yang baik. Risiko dan keuntungan seimbang."
    elif sharpe < 2.0:
        sharpe_label = "Sangat Worth-It"
        sharpe_desc = "Portofolio sangat efisien! Komputer menemukan kombinasi yang memberikan hasil maksimal dengan risiko seminimal mungkin."
    else:
        sharpe_label = "Luar Biasa Efisien"
        sharpe_desc = "Sangat optimal! Keuntungan sangat tinggi dengan volatilitas yang sangat terjaga."
        
    layman_sharpe = {
        "value": f"{sharpe:.2f}",
        "label": sharpe_label,
        "description": sharpe_desc
    }
    
    # 6. Format GA Insight
    layman_ga = {
        "insight": "Komputer kami mensimulasikan dan menguji lebih dari 100.000 kombinasi portofolio dalam 500 generasi kecerdasan genetika untuk menemukan alokasi terbaik yang saat ini Anda lihat."
    }
    
    return {
        "capital": f"Rp {capital:,.0f}".replace(",", "."),
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
    Deskripsi ramah pemula untuk jenis aset investasi.
    """
    name_upper = name.upper()
    if "DEPOSITO" in name_upper:
        return "Tabungan jangka pendek bunga tetap yang dijamin pemerintah/LPS. Sangat aman."
    elif "SBN" in name_upper or "ORI" in name_upper:
        return "Surat Berharga Negara. Surat utang yang diterbitkan pemerintah Indonesia. 100% dijamin negara."
    elif "EMAS" in name_upper or "ANTM" in name_upper or "GC=F" in name_upper:
        return "Emas Batangan. Lindung nilai terbaik dari inflasi. Harganya stabil cenderung naik dalam jangka panjang."
    else:
        # Saham
        return f"Saham perusahaan publik ({name}). Kepemilikan bisnis dengan pertumbuhan tinggi namun fluktuatif."
