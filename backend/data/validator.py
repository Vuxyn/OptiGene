import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def validate_assets(df_prices: pd.DataFrame, min_coverage: float = 0.95) -> tuple[pd.DataFrame, list[str]]:
    """
    Validates historical asset price data based on the following criteria:
    1. Minimum listing period of 3 years (must be active since the start of the 2022-01-01 to 2024-12-31 period).
    2. Daily close data coverage >= 95% (percentage of non-NaN data).
    
    Returns:
        df_cleaned: Cleaned asset prices DataFrame containing only valid assets, with NaN gaps filled.
        valid_tickers: List of tickers that passed validation.
    """
    if df_prices.empty:
        logger.error("Empty input DataFrame. No data to validate.")
        return pd.DataFrame(), []

    total_rows = len(df_prices)
    valid_tickers = []
    rejected_reasons = {}

    for col in df_prices.columns:
        series = df_prices[col]
        # 1. Calculate data coverage
        valid_count = series.notna().sum()
        coverage = valid_count / total_rows
        
        # 2. Check if the asset was listed at the start of the period (listing history > 3 years)
        # First valid index must not be NaN, or must be near the start (e.g. within first 5% of rows)
        first_valid_idx = series.first_valid_index()
        is_listed_long_enough = False
        if first_valid_idx is not None:
            first_valid_pos = df_prices.index.get_loc(first_valid_idx)
            # Must be listed within the first 5% of rows in the time period
            if first_valid_pos <= int(total_rows * 0.05):
                is_listed_long_enough = True

        # Evaluate eligibility
        if coverage >= min_coverage and is_listed_long_enough:
            valid_tickers.append(col)
        else:
            reason = []
            if coverage < min_coverage:
                reason.append(f"low coverage ({coverage*100:.1f}%)")
            if not is_listed_long_enough:
                reason.append("listed for less than 3 years (recent IPO)")
            rejected_reasons[col] = " and ".join(reason)

    if rejected_reasons:
        for ticker, reason in rejected_reasons.items():
            logger.warning(f"Ticker {ticker} REJECTED due to: {reason}")
            
    logger.info(f"Validation results: {len(valid_tickers)} / {len(df_prices.columns)} tickers qualified.")
    
    if not valid_tickers:
        logger.error("No tickers met the validation criteria!")
        return pd.DataFrame(), []

    # Filter DataFrame to columns that passed
    df_filtered = df_prices[valid_tickers].copy()
    
    # Fill small missing gaps (e.g., market holidays) with forward fill followed by backward fill
    df_cleaned = df_filtered.ffill().bfill()
    
    return df_cleaned, valid_tickers
