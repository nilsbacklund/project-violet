import math
import numpy as np

from typing import List
from collections import Counter
from Red.reconfiguration.abstract import AbstractReconfigCriterion

def compute_entropy(prob_dist: List[float], base=math.e) -> float:
    return -sum(p * math.log(p, base) for p in prob_dist if p > 0)

def get_prob_dist(data: Counter) -> List[float]:
    total = sum(data.values())
    return [freq / total for freq in data.values()]

VARIABLES = ["techniques", "session_length"]

# TODO: Add moving avg for to increase noise robustness

class EntropyReconfigCriterion(AbstractReconfigCriterion):
    def __init__(self, variable: str, tolerance: float = 1e-2,
            reset_every_reconfig: bool = False):
        assert variable in VARIABLES, f"Variable '{variable}' is not supported. Supported variables: {VARIABLES}"
        self.variable = variable
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
        return abs(self.entropies[-1] - self.entropies[-2]) < self.tolerance

if __name__ == "__main__":
    x = [0, 1, 1, 2, 3, 3, 4, 5, 5, 6, 7, 9]

    # Simple moving average
    def moving_average(x, w):
        return np.convolve(x, np.ones(w), 'valid') / w

    smoothed = moving_average(x, 2)
    diffs = np.diff(smoothed)   
    print(smoothed)