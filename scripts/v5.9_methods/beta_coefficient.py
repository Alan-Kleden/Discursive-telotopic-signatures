"""
Axiodynamics v5.9 - Beta Coefficient Module
============================================

Implements Method D: Coefficient β (Axiological Alignment)
- Semantic similarity via embeddings
- Valence classification
- β computation: β = cos(θ_axio) × sign(valence)
- Angular assignment formula

Author: Alan Kleden
Date: December 2025
Reference: Axiodynamics v5.9 - Section 6.4
"""

import numpy as np
from typing import Tuple, Optional
from sentence_transformers import SentenceTransformer


class BetaCoefficientCalculator:
    """
    Computes axiological alignment coefficient β and converts to angular position.
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize with sentence embedding model.
        
        Parameters:
        -----------
        model_name : str
            Name of sentence-transformers model
            Default: 'all-MiniLM-L6-v2' (384-dim, fast, multilingual)
        """
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
    
    def compute_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Compute cosine similarity between two texts.
        
        Parameters:
        -----------
        text1, text2 : str
            Input texts (mémotion and telos descriptions)
        
        Returns:
        --------
        float : Cosine similarity ∈ [-1, +1]
        """
        emb1 = self.model.encode(text1)
        emb2 = self.model.encode(text2)
        
        similarity = np.dot(emb1, emb2) / (
            np.linalg.norm(emb1) * np.linalg.norm(emb2)
        )
        
        return float(similarity)
    
    def compute_axiological_distance(self, memotion_text: str, 
                                    telos_text: str) -> float:
        """
        Compute axiological distance angle θ_axio from semantic similarity.
        
        Parameters:
        -----------
        memotion_text : str
            Utterance expressing mémotion
        telos_text : str
            Description of situational telos
        
        Returns:
        --------
        float : Axiological distance θ_axio in degrees [0, 180]
        """
        similarity = self.compute_semantic_similarity(memotion_text, telos_text)
        
        # Clamp to valid range for arccos
        similarity = np.clip(similarity, -1.0, 1.0)
        
        # θ_axio = arccos(similarity)
        theta_axio_rad = np.arccos(similarity)
        theta_axio_deg = np.rad2deg(theta_axio_rad)
        
        return theta_axio_deg
    
    @staticmethod
    def classify_valence(text: str, method: str = 'manual') -> int:
        """
        Classify affective valence of text.
        
        Parameters:
        -----------
        text : str
            Input text
        method : str
            'manual' (requires human input) or 'lexicon' (simple heuristic)
        
        Returns:
        --------
        int : +1 (positive), -1 (negative), 0 (neutral)
        
        Note:
        -----
        For production use, integrate sentiment analysis API
        (e.g., OpenAI, HuggingFace transformers)
        """
        if method == 'manual':
            print(f"\nText: '{text}'")
            valence_input = input("Valence (+1 positive / -1 negative / 0 neutral): ")
            return int(valence_input)
        
        elif method == 'lexicon':
            # Simple lexicon-based (for demo only)
            positive_words = ['love', 'hope', 'excited', 'trust', 'support']
            negative_words = ['fear', 'worry', 'guilt', 'terrified', 'angry']
            
            text_lower = text.lower()
            
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)
            
            if pos_count > neg_count:
                return +1
            elif neg_count > pos_count:
                return -1
            else:
                return 0
        
        else:
            raise ValueError(f"Unknown valence method: {method}")
    
    def compute_beta(self, memotion_text: str, telos_text: str, 
                    valence_sign: Optional[int] = None,
                    valence_method: str = 'manual') -> Tuple[float, float, int]:
        """
        Compute β coefficient.
        
        Parameters:
        -----------
        memotion_text : str
            Utterance expressing mémotion
        telos_text : str
            Description of telos
        valence_sign : int, optional
            If provided, skip valence classification
        valence_method : str
            Method for valence classification ('manual' or 'lexicon')
        
        Returns:
        --------
        Tuple[float, float, int] :
            - β coefficient
            - θ_axio (axiological distance, degrees)
            - valence_sign (+1, -1, or 0)
        """
        # Step 1: Compute axiological distance
        theta_axio = self.compute_axiological_distance(memotion_text, telos_text)
        
        # Step 2: Classify valence
        if valence_sign is None:
            valence_sign = self.classify_valence(memotion_text, method=valence_method)
        
        # Step 3: Compute β = cos(θ_axio) × sign(valence)
        beta = np.cos(np.deg2rad(theta_axio)) * valence_sign
        
        return beta, theta_axio, valence_sign
    
    @staticmethod
    def beta_to_angle(beta: float, theta_base: float = 0.0, 
                     delta_theta: float = 90.0) -> float:
        """
        Convert β coefficient to angular position θ.
        
        Formula: θ = sign(β) · θ_base · |β| + Δθ · (1 - |β|)
        
        Parameters:
        -----------
        beta : float
            Axiological alignment coefficient [-1, +1]
        theta_base : float
            Reference angle for perfect alignment (default: 0° for Fc)
        delta_theta : float
            Contextual perturbation for ambiguous cases (default: 90°)
        
        Returns:
        --------
        float : Angular position θ in degrees [0, 360)
        """
        theta = (np.sign(beta) * theta_base * np.abs(beta) + 
                delta_theta * (1 - np.abs(beta)))
        
        # Normalize to [0, 360)
        theta = theta % 360
        
        return theta
    
    def memotion_to_angle(self, memotion_text: str, telos_text: str,
                         valence_sign: Optional[int] = None,
                         valence_method: str = 'manual',
                         theta_base: float = 0.0,
                         delta_theta: float = 90.0) -> dict:
        """
        Complete pipeline: mémotion text → angular position.
        
        Parameters:
        -----------
        memotion_text : str
            Utterance expressing mémotion
        telos_text : str
            Description of telos
        valence_sign : int, optional
            Pre-classified valence
        valence_method : str
            Method for valence classification
        theta_base : float
            Reference angle
        delta_theta : float
            Ambivalence angle
        
        Returns:
        --------
        dict : Complete results including β, θ_axio, valence, and final angle
        """
        # Compute β
        beta, theta_axio, valence = self.compute_beta(
            memotion_text, telos_text, valence_sign, valence_method
        )
        
        # Convert to angle
        theta = self.beta_to_angle(beta, theta_base, delta_theta)
        
        # Classification
        if theta < 90:
            classification = "Strong Fc"
        elif 90 <= theta < 120:
            classification = "Weak Fc / Ambivalent"
        elif 120 <= theta < 240:
            classification = "Inhibitory (Fi)"
        else:
            classification = "Weak Fi / Defensive"
        
        return {
            'memotion': memotion_text,
            'telos': telos_text,
            'beta': beta,
            'theta_axio_deg': theta_axio,
            'valence_sign': valence,
            'theta_final_deg': theta,
            'classification': classification
        }


# Example usage
if __name__ == "__main__":
    print("=== Axiodynamics v5.9 - Beta Coefficient Demo ===\n")
    
    # Initialize calculator
    calc = BetaCoefficientCalculator()
    
    # Example scenario: Good Samaritan dilemma (Section 8.2)
    telos = "Stop to help the accident victim"
    
    memotion_examples = [
        ("I took an oath to help anyone in medical distress", +1),
        ("My surgery patient could die if I'm late", -1),
        ("I feel guilty leaving someone injured on the roadside", +1),  # guilt → pro-telos
        ("This accident victim's injuries look minor, probably not critical", +1)
    ]
    
    results = []
    
    for mem_text, valence in memotion_examples:
        result = calc.memotion_to_angle(
            memotion_text=mem_text,
            telos_text=telos,
            valence_sign=valence,
            valence_method='lexicon'  # Pre-classified for demo
        )
        results.append(result)
        
        print(f"Mémotion: {mem_text[:50]}...")
        print(f"  β = {result['beta']:.3f}")
        print(f"  θ_axio = {result['theta_axio_deg']:.1f}°")
        print(f"  θ_final = {result['theta_final_deg']:.1f}°")
        print(f"  Classification: {result['classification']}\n")
    
    print("\n=== Method Comparison ===")
    print("\nExpected angles from Section 8.6 (Method D):")
    print("m1 (oath):          11° (Strong Fc)")
    print("m2 (surgery):       175° (Strong Fi, manual override)")
    print("m3 (guilt):         25° (Moderate Fc)")
    print("m4 (minor injury):  39° (Weak Fc)")
    
    print("\nComputed angles:")
    for i, r in enumerate(results, 1):
        print(f"m{i}: {r['theta_final_deg']:.0f}° ({r['classification']})")
    
    print("\n=== Convergence Check ===")
    # Compare with Method A gold standard (from Section 8.3)
    method_A_angles = [10, 170, 25, 55]
    method_D_angles = [r['theta_final_deg'] for r in results]
    
    from circular_stats import circular_correlation, rmse_angular
    
    rho = circular_correlation(
        np.array(method_A_angles),
        np.array(method_D_angles)
    )
    
    rmsae = rmse_angular(
        np.array(method_A_angles),
        np.array(method_D_angles)
    )
    
    print(f"ρ(Method A, Method D) = {rho:.3f}")
    print(f"RMSAE = {rmsae:.1f}°")
    
    if rho >= 0.60:
        print("✓ Acceptable convergence (ρ ≥ 0.60)")
    else:
        print("✗ Poor convergence - investigate discrepancy")
