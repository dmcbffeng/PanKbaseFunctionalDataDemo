"""Statistical utility functions"""
import numpy as np
from scipy import stats
from typing import Tuple, Optional


def pearson_confidence_interval(
    r: float, 
    n: int, 
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate confidence interval for Pearson correlation coefficient.
    
    Uses Fisher z-transformation.
    
    Args:
        r: Correlation coefficient
        n: Sample size
        confidence: Confidence level (default 0.95 for 95% CI)
        
    Returns:
        Tuple of (lower, upper) confidence bounds
    """
    if n < 4:
        return (np.nan, np.nan)
    
    # Fisher z-transformation
    z = np.arctanh(r)
    se = 1 / np.sqrt(n - 3)
    
    # Z-score for confidence level
    alpha = 1 - confidence
    z_crit = stats.norm.ppf(1 - alpha / 2)
    
    # Confidence interval in z-space
    z_lower = z - z_crit * se
    z_upper = z + z_crit * se
    
    # Transform back
    r_lower = np.tanh(z_lower)
    r_upper = np.tanh(z_upper)
    
    return (r_lower, r_upper)


def cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size for two groups.
    
    Args:
        group1: First group values
        group2: Second group values
        
    Returns:
        Cohen's d effect size
    """
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (np.mean(group1) - np.mean(group2)) / pooled_std


def eta_squared(f_statistic: float, df_between: int, df_within: int) -> float:
    """
    Calculate eta-squared effect size from ANOVA F-statistic.
    
    Args:
        f_statistic: F-statistic from ANOVA
        df_between: Degrees of freedom between groups
        df_within: Degrees of freedom within groups
        
    Returns:
        Eta-squared effect size
    """
    return (f_statistic * df_between) / (f_statistic * df_between + df_within)


def benjamini_hochberg(p_values: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        p_values: Array of p-values
        alpha: Significance level (default 0.05)
        
    Returns:
        Array of adjusted p-values (q-values)
    """
    n = len(p_values)
    if n == 0:
        return np.array([])
    
    # Sort p-values and track original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate BH critical values
    ranks = np.arange(1, n + 1)
    bh_critical = (ranks / n) * alpha
    
    # Calculate adjusted p-values
    adjusted_p = np.minimum(1, sorted_p * n / ranks)
    
    # Make monotonically increasing from the end
    adjusted_p = np.minimum.accumulate(adjusted_p[::-1])[::-1]
    
    # Restore original order
    result = np.empty(n)
    result[sorted_indices] = adjusted_p
    
    return result


def bootstrap_ci(
    data: np.ndarray,
    statistic_func,
    n_bootstrap: int = 1000,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate bootstrap confidence interval for any statistic.
    
    Args:
        data: Input data array
        statistic_func: Function that calculates the statistic
        n_bootstrap: Number of bootstrap samples
        confidence: Confidence level
        
    Returns:
        Tuple of (lower, upper) confidence bounds
    """
    n = len(data)
    bootstrap_stats = np.zeros(n_bootstrap)
    
    for i in range(n_bootstrap):
        sample = np.random.choice(data, size=n, replace=True)
        bootstrap_stats[i] = statistic_func(sample)
    
    alpha = 1 - confidence
    lower = np.percentile(bootstrap_stats, 100 * alpha / 2)
    upper = np.percentile(bootstrap_stats, 100 * (1 - alpha / 2))
    
    return (lower, upper)
