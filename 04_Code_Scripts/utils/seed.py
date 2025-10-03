# seed.py — seeds reproductibles
from __future__ import annotations
import os, random
import numpy as np

def seed_all(seed: int = 1337) -> None:
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        torch.use_deterministic_algorithms(False)  # CPU ok, pas besoin de full determinism
    except Exception:
        pass
