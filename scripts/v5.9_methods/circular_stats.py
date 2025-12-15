"""
Axiodynamics v5.9 - Circular Statistics Module
===============================================

Implements circular statistical methods for angular data analysis:
- Circular Cohen's kappa (inter-annotator agreement)
- Circular correlation coefficient
- Rayleigh test for uniformity
- Bootstrap confidence intervals
- Mean resultant length and circular standard deviation

Author: Alan Kleden
Date: December 2025
Reference: Axiodynamics v5.9 - Angular Semantics and Validation Protocols
"""

import numpy as np
from scipy import stats
from typing import List, Tuple, Optional


def circular_distance(theta1: float, theta2: float) -> float:
    """
    Compute circular distance between two angles (shortest arc).
    
    Parameters:
    -----------
    theta1, theta2 : float
        Angles in degrees [0, 360)
    
    Returns:
    --------
    float : Circular distance in degrees
    """
    diff = np.abs(theta1 - theta2)
    return np.minimum(diff, 360 - diff)


def circular_mean(angles: np.ndarray) -> float:
    """
    Compute circular mean of angles.
    
    Parameters:
    -----------
    angles : np.ndarray
        Array of angles in degrees
    
    Returns:
    --------
    float : Circular mean in degrees [0, 360)
    """
    angles_rad = np.deg2rad(angles)
    sin_sum = np.sum(np.sin(angles_rad))
    cos_sum = np.sum(np.cos(angles_rad))
    mean_rad = np.arctan2(sin_sum, cos_sum)
    return np.rad2deg(mean_rad) % 360


def mean_resultant_length(angles: np.ndarray, weights: Optional[np.ndarray] = None) -> float:
    """
    Compute mean resultant length (concentration metric).
    
    Parameters:
    -----------
    angles : np.ndarray
        Array of angles in degrees
    weights : np.ndarray, optional
        Weights for each angle (default: uniform)
    
    Returns:
    --------
    float : Mean resultant length R̄ ∈ [0, 1]
    """
    angles_rad = np.deg2rad(angles)
    
    if weights is None:
        weights = np.ones(len(angles))
    
    weights = weights / np.sum(weights)  # Normalize
    
    sin_sum = np.sum(weights * np.sin(angles_rad))
    cos_sum = np.sum(weights * np.cos(angles_rad))
    
    R_bar = np.sqrt(sin_sum**2 + cos_sum**2)
    return R_bar


def circular_std(angles: np.ndarray) -> float:
    """
    Compute circular standard deviation.
    
    Parameters:
    -----------
    angles : np.ndarray
        Array of angles in degrees
    
    Returns:
    --------
    float : Circular SD in degrees
    """
    R_bar = mean_resultant_length(angles)
    sigma_circ = np.sqrt(-2 * np.log(R_bar))
    return np.rad2deg(sigma_circ)


def rayleigh_test(angles: np.ndarray, alpha: float = 0.05) -> Tuple[float, float, bool]:
    """
    Rayleigh test for uniformity (proto-telos gate).
    
    H0: Angles uniformly distributed (no directional clustering)
    H1: Non-uniform distribution (proto-telos present)
    
    Parameters:
    -----------
    angles : np.ndarray
        Array of angles in degrees
    alpha : float
        Significance level (default: 0.05)
    
    Returns:
    --------
    Tuple[float, float, bool] :
        - Z statistic
        - p-value
        - is_significant (True if reject H0)
    """
    N = len(angles)
    R_bar = mean_resultant_length(angles)
    
    Z = N * R_bar**2
    
    # Asymptotic approximation (valid for N >= 8)
    p_value = np.exp(-Z)
    
    is_significant = p_value < alpha
    
    return Z, p_value, is_significant


def circular_cohen_kappa(theta1: np.ndarray, theta2: np.ndarray, 
                         epsilon: float = 20.0) -> float:
    """
    Circular Cohen's kappa for inter-annotator agreement.
    
    Parameters:
    -----------
    theta1, theta2 : np.ndarray
        Arrays of angles (degrees) from two annotators
    epsilon : float
        Tolerance threshold in degrees (default: 20°)
    
    Returns:
    --------
    float : Circular kappa coefficient
    
    Interpretation:
    ---------------
    κ < 0.40  : Poor agreement
    0.40-0.60 : Moderate agreement
    0.60-0.80 : Good agreement
    κ >= 0.80 : Excellent agreement
    """
    N = len(theta1)
    
    # Compute circular distances
    circ_dists = np.array([circular_distance(theta1[i], theta2[i]) 
                          for i in range(N)])
    
    # Observed agreement
    A_o = np.mean(circ_dists <= epsilon)
    
    # Expected agreement (chance baseline)
    # Proportion of circle within tolerance
    A_e = epsilon / 180.0
    
    # Cohen's kappa
    if A_e >= 1.0:
        return 1.0  # Perfect agreement by definition
    
    kappa_circ = (A_o - A_e) / (1.0 - A_e)
    return kappa_circ


def circular_correlation(theta1: np.ndarray, theta2: np.ndarray) -> float:
    """
    Circular-circular correlation coefficient.
    
    Parameters:
    -----------
    theta1, theta2 : np.ndarray
        Arrays of angles in degrees
    
    Returns:
    --------
    float : Circular correlation ρ_circ ∈ [-1, 1]
    
    Reference: Jammalamadaka & SenGupta (2001)
    """
    theta1_rad = np.deg2rad(theta1)
    theta2_rad = np.deg2rad(theta2)
    
    # Circular means
    mean1 = np.angle(np.mean(np.exp(1j * theta1_rad)))
    mean2 = np.angle(np.mean(np.exp(1j * theta2_rad)))
    
    # Deviations from circular mean
    sin1 = np.sin(theta1_rad - mean1)
    sin2 = np.sin(theta2_rad - mean2)
    
    # Correlation
    numerator = np.sum(sin1 * sin2)
    denominator = np.sqrt(np.sum(sin1**2) * np.sum(sin2**2))
    
    if denominator == 0:
        return 0.0
    
    rho_circ = numerator / denominator
    return rho_circ


def bootstrap_circular_ci(angles: np.ndarray, n_bootstrap: int = 1000, 
                         alpha: float = 0.05) -> Tuple[float, float, float]:
    """
    Bootstrap confidence interval for circular mean.
    
    Parameters:
    -----------
    angles : np.ndarray
        Array of angles in degrees
    n_bootstrap : int
        Number of bootstrap iterations (default: 1000)
    alpha : float
        Significance level for CI (default: 0.05 for 95% CI)
    
    Returns:
    --------
    Tuple[float, float, float] :
        - Circular mean (degrees)
        - Lower CI bound (degrees)
        - Upper CI bound (degrees)
    """
    bootstrap_means = []
    N = len(angles)
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        sample_idx = np.random.choice(N, size=N, replace=True)
        sample = angles[sample_idx]
        
        # Compute circular mean
        mean_sample = circular_mean(sample)
        bootstrap_means.append(mean_sample)
    
    bootstrap_means = np.array(bootstrap_means)
    
    # Original circular mean
    mean_original = circular_mean(angles)
    
    # Percentile CI
    CI_lower = np.percentile(bootstrap_means, 100 * alpha / 2)
    CI_upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))
    
    return mean_original, CI_lower, CI_upper


def von_mises_concentration(R_bar: float) -> float:
    """
    Estimate von Mises concentration parameter κ from mean resultant length.
    
    Parameters:
    -----------
    R_bar : float
        Mean resultant length
    
    Returns:
    --------
    float : Concentration parameter κ
    
    Approximation valid for R_bar > 0.7
    """
    if R_bar >= 1.0:
        return np.inf
    
    kappa = (-2 * np.log(1 - R_bar)) / (1 - R_bar**2)
    return kappa


def rmse_angular(theta1: np.ndarray, theta2: np.ndarray) -> float:
    """
    Root Mean Squared Angular Error (RMSAE).
    
    Parameters:
    -----------
    theta1, theta2 : np.ndarray
        Arrays of angles in degrees
    
    Returns:
    --------
    float : RMSAE in degrees
    
    Interpretation:
    ---------------
    RMSAE < 20°  : Excellent agreement
    20-40°       : Moderate agreement
    RMSAE >= 40° : Poor agreement
    """
    circ_dists = np.array([circular_distance(theta1[i], theta2[i]) 
                          for i in range(len(theta1))])
    
    rmsae = np.sqrt(np.mean(circ_dists**2))
    return rmsae


# Example usage
if __name__ == "__main__":
    # Generate sample data
    np.random.seed(42)
    
    # Two annotators with good agreement
    theta_annotator1 = np.array([10, 25, 170, 55, 15, 180, 30, 50])
    theta_annotator2 = np.array([5, 30, 177, 60, 10, 175, 25, 45])
    
    print("=== Axiodynamics v5.9 - Circular Statistics Demo ===\n")
    
    # Circular mean
    mean1 = circular_mean(theta_annotator1)
    print(f"Circular mean (Annotator 1): {mean1:.2f}°")
    
    # Mean resultant length
    R_bar = mean_resultant_length(theta_annotator1)
    print(f"Mean resultant length: {R_bar:.3f}")
    
    # Circular SD
    sigma = circular_std(theta_annotator1)
    print(f"Circular SD: {sigma:.2f}°\n")
    
    # Rayleigh test
    Z, p_val, significant = rayleigh_test(theta_annotator1)
    print(f"Rayleigh test: Z = {Z:.3f}, p = {p_val:.4f}")
    print(f"Proto-telos detected: {significant}\n")
    
    # Inter-annotator agreement
    kappa = circular_cohen_kappa(theta_annotator1, theta_annotator2, epsilon=20)
    print(f"Circular Cohen's κ: {kappa:.3f}")
    
    # Circular correlation
    rho = circular_correlation(theta_annotator1, theta_annotator2)
    print(f"Circular correlation: {rho:.3f}")
    
    # RMSAE
    rmsae = rmse_angular(theta_annotator1, theta_annotator2)
    print(f"RMSAE: {rmsae:.2f}°\n")
    
    # Bootstrap CI
    mean_boot, CI_low, CI_high = bootstrap_circular_ci(theta_annotator1, n_bootstrap=1000)
    print(f"Bootstrap 95% CI: [{CI_low:.2f}°, {CI_high:.2f}°]")
    print(f"CI width: {CI_high - CI_low:.2f}°")
