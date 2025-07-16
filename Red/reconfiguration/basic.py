from Red.reconfiguration.abstract import AbstractReconfigCriterion

class BasicReconfigCriterion(AbstractReconfigCriterion):
    def __init__(self, interval: int, reset_every_reconfig: bool = False):
        assert self.interval >= 0, f"The interval to reconfig must be non-negative ({interval} < 0)"
        self.interval = interval
        super().__init__(reset_every_reconfig)

    def reset(self):
        self.num_sessions = 0

    def update(self, session):
        self.num_sessions += 1
        
    def should_reconfigure(self):
        return self.num_sessions >= self.interval