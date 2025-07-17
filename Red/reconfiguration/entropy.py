import math
import numpy as np

from typing import List
from collections import Counter
from Red.reconfiguration.abstract import AbstractReconfigCriterion

VARIABLES = ["techniques", "session_length"]

def compute_entropy(prob_dist: List[float], base=math.e) -> float:
    return -sum(p * math.log(p, base) for p in prob_dist if p > 0)

def get_prob_dist(data: Counter) -> List[float]:
    total = sum(data.values())
    return [freq / total for freq in data.values()]

def moving_average(x: np.ndarray, w: int):
    return np.convolve(x, np.ones(w), 'valid') / w

class EntropyReconfigCriterion(AbstractReconfigCriterion):
    def __init__(self, variable: str, tolerance: float = 1e-2,
            window_size: int = 1, reset_every_reconfig: bool = False):
        assert variable in VARIABLES, f"Variable '{variable}' is not supported. Supported variables: {VARIABLES}"
        self.variable = variable
        assert window_size >= 0, f"Window size must be non-negative ({window_size} < 0)"
        self.window_size = window_size
        self.tolerance = tolerance
        super().__init__(reset_every_reconfig)

    def reset(self):
        self.entropies: List[float] = [0]
        self.counter = Counter()

    def update(self, session):
        match self.variable:
            case "techniques":
                for command_entry in session.get("full_session", []):
                    if "technique" in command_entry and command_entry["technique"]:
                        self.counter.update([command_entry["technique"]])
            case "session_length":
                raise NotImplementedError("My bad lol // Sackarias")

        entropy_value = compute_entropy(self.counter)
        self.entropies.append(entropy_value)
        
    def should_reconfigure(self):
        if len(self.entropies) < self.window_size:
            return False
        
        smoothed_entropies = moving_average(self.entropies, self.window_size)
        return abs(smoothed_entropies[-1] - smoothed_entropies[-2]) < self.tolerance