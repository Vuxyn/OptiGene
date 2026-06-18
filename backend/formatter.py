def format_layman_results(results: dict, capital: float, duration_years: int = 1) -> dict:
    """
    Converts technical portfolio optimization results into a layman-friendly format
    understandable by investment beginners.
    """
    weights = results["weights"]
    expected_return = results["return"]
    volatility = results["volatility"]
    sharpe = results["sharpe"]
    max_dd = results["max_drawdown"]
    
    # 1. Format Asset Allocation to IDR
    allocation_details = []
    
    # Category labels
    asset_names = results.get("asset_names", ["Time Deposit", "Government Bonds (SBN)", "Gold (ANTM)"] + [f"Stock {i}" for i in range(len(weights)-3)])
    
    for name, weight in zip(asset_names, weights):
        if weight > 0.001:  # Display only if allocation > 0.1%
            allocated_money = capital * weight
            allocation_details.append({
                "asset": name,
                "percentage": f"{weight * 100:.2f}%",
                "nominal": f"IDR {allocated_money:,.0f}",
                "description": _get_asset_description(name)
            })
            
    # 2. Format Returns
    annual_profit = capital * expected_return
    # Calculate compounded returns
    compounded_value = capital * ((1 + expected_return) ** duration_years)
    compounded_profit = compounded_value - capital
    
    layman_return = {
        "percentage": f"{expected_return * 100:.2f}% per year",
        "description": f"Your capital of IDR {capital:,.0f} is projected to grow to IDR {compounded_value:,.0f} in {duration_years} year(s) (accumulating a profit of IDR {compounded_profit:,.0f}).",
        "summary": f"Estimated profit: +IDR {annual_profit:,.0f}/year"
    }
    
    # 3. Format Risk (Volatility)
    if volatility < 0.05:
        vol_label = "Very Low (Safe)"
        vol_desc = "Price fluctuations are extremely minor. Highly stable, behaving similarly to a standard savings account."
    elif volatility < 0.10:
        vol_label = "Low (Stable)"
        vol_desc = "Small price fluctuations. Suitable for investors who prefer stable growth without sudden value drops."
    elif volatility < 0.18:
        vol_label = "Medium (Moderate)"
        vol_desc = "Normal price fluctuations. Expect moderate short-term variations with reliable medium-term security."
    else:
        vol_label = "High (Aggressive)"
        vol_desc = "Prices fluctuate rapidly. High return potential, but require tolerance for significant market swings."
        
    layman_volatility = {
        "label": vol_label,
        "percentage": f"{volatility * 100:.2f}%",
        "description": vol_desc
    }
    
    # 4. Format Worst-Case Loss (Max Drawdown)
    potential_loss = capital * max_dd
    layman_drawdown = {
        "percentage": f"{max_dd * 100:.2f}%",
        "nominal": f"IDR {potential_loss:,.0f}",
        "description": f"In the worst-case historical market scenario (e.g., a financial crisis), this portfolio experienced a maximum temporary drop of {max_dd * 100:.1f}%, equivalent to IDR {potential_loss:,.0f}. However, this decline was temporary before recovering."
    }
    
    # 5. Format Portfolio Efficiency (Sharpe Ratio)
    if sharpe < 0.5:
        sharpe_label = "Low Efficiency"
        sharpe_desc = "The expected returns do not sufficiently compensate for the level of risk taken."
    elif sharpe < 1.2:
        sharpe_label = "Fair Trade-off"
        sharpe_desc = "A balanced portfolio combination where the returns are fair relative to the volatility."
    elif sharpe < 2.0:
        sharpe_label = "Highly Efficient"
        sharpe_desc = "Extremely efficient! The algorithm found an optimal mix that maximizes returns while keeping volatility low."
    else:
        sharpe_label = "Outstandingly Optimal"
        sharpe_desc = "Superb portfolio design! Exceptional returns achieved with highly controlled overall risk."
        
    layman_sharpe = {
        "value": f"{sharpe:.2f}",
        "label": sharpe_label,
        "description": sharpe_desc
    }
    
    # 6. Format GA Insight
    layman_ga = {
        "insight": "Our system simulated and evaluated over 100,000 portfolio combinations across 500 generations of genetic algorithm optimization to find the best allocation shown above."
    }
    
    return {
        "capital": f"IDR {capital:,.0f}",
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
    Layman-friendly description for types of assets.
    """
    name_upper = name.upper()
    if "DEPOSITO" in name_upper or "TIME DEPOSIT" in name_upper:
        return "Fixed-rate short-term savings guaranteed by deposit insurance (LPS). Highly secure."
    elif "SBN" in name_upper or "ORI" in name_upper or "BOND" in name_upper:
        return "Government Securities. Debt instruments issued by the Republic of Indonesia. 100% state-backed."
    elif "EMAS" in name_upper or "ANTM" in name_upper or "GC=F" in name_upper or "GOLD" in name_upper:
        return "Gold Bullion. The ultimate hedge against inflation and systemic risk. Historically stable in the long term."
    else:
        # Stock
        return f"Publicly traded stock ({name}). High growth potential through business equity, subject to market swings."
