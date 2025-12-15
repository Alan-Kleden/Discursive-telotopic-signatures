"""
Axiodynamics v5.9 - Method Comparison Module
=============================================

Implements cross-method validation metrics:
- Pairwise correlation matrix (Methods A/B/C/D)
- RMSAE (Root Mean Squared Angular Error)
- Bland-Altman plots for angular data
- Convergent validity assessment

Author: Alan Kleden
Date: December 2025
Reference: Axiodynamics v5.9 - Section 7.4
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple
from circular_stats import (
    circular_correlation, 
    rmse_angular,
    circular_mean,
    circular_distance
)


class MethodComparator:
    """
    Compares angular estimates across multiple estimation methods.
    """
    
    def __init__(self):
        self.methods = {}
        self.method_names = []
    
    def add_method(self, method_name: str, angles: np.ndarray):
        """
        Add angular estimates from a method.
        
        Parameters:
        -----------
        method_name : str
            Name of method (e.g., "Method A", "Method B", etc.)
        angles : np.ndarray
            Array of angular estimates in degrees
        """
        self.methods[method_name] = np.array(angles)
        self.method_names.append(method_name)
    
    def compute_correlation_matrix(self) -> Tuple[np.ndarray, List[str]]:
        """
        Compute pairwise circular correlation matrix.
        
        Returns:
        --------
        Tuple[np.ndarray, List[str]] :
            - Correlation matrix (K × K)
            - Method names
        """
        K = len(self.method_names)
        corr_matrix = np.eye(K)
        
        for i in range(K):
            for j in range(i + 1, K):
                method_i = self.method_names[i]
                method_j = self.method_names[j]
                
                rho = circular_correlation(
                    self.methods[method_i],
                    self.methods[method_j]
                )
                
                corr_matrix[i, j] = rho
                corr_matrix[j, i] = rho
        
        return corr_matrix, self.method_names
    
    def compute_rmsae_matrix(self) -> Tuple[np.ndarray, List[str]]:
        """
        Compute pairwise RMSAE matrix.
        
        Returns:
        --------
        Tuple[np.ndarray, List[str]] :
            - RMSAE matrix (K × K)
            - Method names
        """
        K = len(self.method_names)
        rmsae_matrix = np.zeros((K, K))
        
        for i in range(K):
            for j in range(K):
                if i == j:
                    rmsae_matrix[i, j] = 0.0
                else:
                    method_i = self.method_names[i]
                    method_j = self.method_names[j]
                    
                    rmsae = rmse_angular(
                        self.methods[method_i],
                        self.methods[method_j]
                    )
                    
                    rmsae_matrix[i, j] = rmsae
        
        return rmsae_matrix, self.method_names
    
    def bland_altman_angular(self, method1: str, method2: str, 
                            save_path: str = None):
        """
        Create Bland-Altman plot for angular data.
        
        Parameters:
        -----------
        method1, method2 : str
            Names of methods to compare
        save_path : str, optional
            Path to save figure
        """
        angles1 = self.methods[method1]
        angles2 = self.methods[method2]
        
        # Circular means
        means = np.array([circular_mean(np.array([angles1[i], angles2[i]])) 
                         for i in range(len(angles1))])
        
        # Circular differences
        diffs = np.array([circular_distance(angles1[i], angles2[i]) 
                         for i in range(len(angles1))])
        
        # Mean difference and limits of agreement
        mean_diff = np.mean(diffs)
        std_diff = np.std(diffs)
        upper_loa = mean_diff + 1.96 * std_diff
        lower_loa = mean_diff - 1.96 * std_diff
        
        # Plot
        plt.figure(figsize=(10, 6))
        plt.scatter(means, diffs, alpha=0.6, s=50)
        plt.axhline(mean_diff, color='blue', linestyle='--', 
                   label=f'Mean difference: {mean_diff:.2f}°')
        plt.axhline(upper_loa, color='red', linestyle='--', 
                   label=f'Upper LoA: {upper_loa:.2f}°')
        plt.axhline(lower_loa, color='red', linestyle='--', 
                   label=f'Lower LoA: {lower_loa:.2f}°')
        
        plt.xlabel('Mean angle (degrees)', fontsize=12)
        plt.ylabel('Angular difference (degrees)', fontsize=12)
        plt.title(f'Bland-Altman Plot: {method1} vs {method2}', fontsize=14)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
        
        return mean_diff, lower_loa, upper_loa
    
    def assess_convergence(self, rho_threshold: float = 0.60, 
                          rmsae_threshold: float = 40.0) -> Dict:
        """
        Assess convergent validity across all methods.
        
        Parameters:
        -----------
        rho_threshold : float
            Minimum acceptable correlation (default: 0.60)
        rmsae_threshold : float
            Maximum acceptable RMSAE in degrees (default: 40°)
        
        Returns:
        --------
        Dict : Convergence assessment report
        """
        corr_matrix, names = self.compute_correlation_matrix()
        rmsae_matrix, _ = self.compute_rmsae_matrix()
        
        K = len(names)
        
        # Extract upper triangle (exclude diagonal)
        corr_values = []
        rmsae_values = []
        
        for i in range(K):
            for j in range(i + 1, K):
                corr_values.append(corr_matrix[i, j])
                rmsae_values.append(rmsae_matrix[i, j])
        
        corr_values = np.array(corr_values)
        rmsae_values = np.array(rmsae_values)
        
        # Assessment
        high_convergence = np.sum(corr_values >= rho_threshold)
        acceptable_rmsae = np.sum(rmsae_values <= rmsae_threshold)
        total_pairs = len(corr_values)
        
        report = {
            'n_methods': K,
            'n_pairs': total_pairs,
            'correlation_matrix': corr_matrix,
            'rmsae_matrix': rmsae_matrix,
            'method_names': names,
            'mean_correlation': np.mean(corr_values),
            'mean_rmsae': np.mean(rmsae_values),
            'high_convergence_pairs': high_convergence,
            'acceptable_rmsae_pairs': acceptable_rmsae,
            'convergence_rate': high_convergence / total_pairs,
            'rmsae_success_rate': acceptable_rmsae / total_pairs
        }
        
        # Overall verdict
        if report['convergence_rate'] >= 0.75 and report['rmsae_success_rate'] >= 0.75:
            report['verdict'] = "Strong triangulation ✓"
        elif report['convergence_rate'] >= 0.50:
            report['verdict'] = "Partial convergence (acceptable)"
        else:
            report['verdict'] = "Divergence detected - investigate ✗"
        
        return report
    
    def print_report(self, report: Dict):
        """
        Print convergence assessment report.
        
        Parameters:
        -----------
        report : Dict
            Output from assess_convergence()
        """
        print("=" * 60)
        print("AXIODYNAMICS v5.9 - CROSS-METHOD CONVERGENCE REPORT")
        print("=" * 60)
        print(f"\nNumber of methods: {report['n_methods']}")
        print(f"Number of pairwise comparisons: {report['n_pairs']}")
        
        print("\n--- CORRELATION MATRIX ---")
        names = report['method_names']
        corr_matrix = report['correlation_matrix']
        
        print(f"{'':12}", end='')
        for name in names:
            print(f"{name:12}", end='')
        print()
        
        for i, name in enumerate(names):
            print(f"{name:12}", end='')
            for j in range(len(names)):
                if i == j:
                    print(f"{'—':>12}", end='')
                else:
                    print(f"{corr_matrix[i, j]:12.3f}", end='')
            print()
        
        print("\n--- RMSAE MATRIX (degrees) ---")
        rmsae_matrix = report['rmsae_matrix']
        
        print(f"{'':12}", end='')
        for name in names:
            print(f"{name:12}", end='')
        print()
        
        for i, name in enumerate(names):
            print(f"{name:12}", end='')
            for j in range(len(names)):
                if i == j:
                    print(f"{'—':>12}", end='')
                else:
                    print(f"{rmsae_matrix[i, j]:12.1f}", end='')
            print()
        
        print("\n--- SUMMARY STATISTICS ---")
        print(f"Mean correlation (ρ̄):      {report['mean_correlation']:.3f}")
        print(f"Mean RMSAE:                {report['mean_rmsae']:.1f}°")
        print(f"High convergence pairs:    {report['high_convergence_pairs']}/{report['n_pairs']} ({report['convergence_rate']*100:.1f}%)")
        print(f"Acceptable RMSAE pairs:    {report['acceptable_rmsae_pairs']}/{report['n_pairs']} ({report['rmsae_success_rate']*100:.1f}%)")
        
        print(f"\n--- VERDICT ---")
        print(f"{report['verdict']}")
        
        print("\n" + "=" * 60)


# Example usage
if __name__ == "__main__":
    print("=== Axiodynamics v5.9 - Method Comparison Demo ===\n")
    
    # Load example data from Section 8.7 (Good Samaritan dilemma)
    # Four mémotions, four estimation methods
    
    method_A_angles = np.array([10, 170, 25, 55])   # Expert annotation
    method_B_angles = np.array([5, 177, 14, 40])    # Semantic embedding
    method_C_angles = np.array([9, 180, 30, 40])    # Axiotypic anchoring
    method_D_angles = np.array([11, 175, 25, 39])   # Beta coefficient
    
    # Initialize comparator
    comparator = MethodComparator()
    comparator.add_method("Method A", method_A_angles)
    comparator.add_method("Method B", method_B_angles)
    comparator.add_method("Method C", method_C_angles)
    comparator.add_method("Method D", method_D_angles)
    
    # Compute convergence report
    report = comparator.assess_convergence(rho_threshold=0.60, rmsae_threshold=40.0)
    
    # Print report
    comparator.print_report(report)
    
    # Bland-Altman plot example
    print("\nGenerating Bland-Altman plot for Method A vs Method D...")
    mean_diff, lower_loa, upper_loa = comparator.bland_altman_angular(
        "Method A", "Method D", 
        save_path=None  # Set to filepath to save
    )
    
    print(f"\nBland-Altman statistics:")
    print(f"  Mean difference: {mean_diff:.2f}°")
    print(f"  95% LoA: [{lower_loa:.2f}°, {upper_loa:.2f}°]")
    
    # Individual pairwise comparisons
    print("\n--- PAIRWISE DETAILS ---")
    
    for i in range(len(comparator.method_names)):
        for j in range(i + 1, len(comparator.method_names)):
            method_i = comparator.method_names[i]
            method_j = comparator.method_names[j]
            
            rho = report['correlation_matrix'][i, j]
            rmsae = report['rmsae_matrix'][i, j]
            
            print(f"\n{method_i} ↔ {method_j}:")
            print(f"  ρ = {rho:.3f}", end='')
            
            if rho >= 0.80:
                print(" (excellent)")
            elif rho >= 0.60:
                print(" (good)")
            elif rho >= 0.40:
                print(" (moderate)")
            else:
                print(" (poor)")
            
            print(f"  RMSAE = {rmsae:.1f}°", end='')
            
            if rmsae < 20:
                print(" (excellent)")
            elif rmsae < 40:
                print(" (acceptable)")
            else:
                print(" (poor)")
