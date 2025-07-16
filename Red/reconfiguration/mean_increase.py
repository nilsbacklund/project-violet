from typing import List
from Red.reconfiguration.abstract import AbstractReconfigCriterion

VARIABLES = ["techniques", "max_session_length"]

class MeanIncreaseReconfigCriterion(AbstractReconfigCriterion):
    def __init__(self, variable: str, tolerance: float = 0.5, window_size: int = 5,
            reset_techniques: bool = True, reset_every_reconfig = False):
        
        assert variable in VARIABLES, f"Variable '{variable}' is not supported. Supported variables: {VARIABLES}"
        self.variable = variable
        assert window_size >= 0, f"Window size must be non-negative ({window_size} < 0)"
        self.tolerance = tolerance
        self.window_size = window_size
        self.reset_techniques = reset_techniques
        super().__init__(reset_every_reconfig)

    def reset(self):
        self.values: List[int] = [0]
        if self.reset_techniques:
            self.techniques: set[str] = {}

    def update(self, session):
        match self.variable:
            case "techniques":
                for command_entry in session.get("full_session", []):
                    if "technique" in command_entry and command_entry["technique"]:
                        self.techniques.add(command_entry["technique"])
                        self.values.append(len(self.techniques))
            case "max_session_length":
                raise NotImplementedError("My bad lol // Sackarias")

    def should_reconfigure(self):
        if len(self.values) < self.window_size:
            return False
        current_value = self.values[-1]
        prev_value = self.values[-self.window_size]
        mean_diff = abs(current_value - prev_value) / self.window_size
        return mean_diff < self.tolerance
