from Red.reconfiguration.abstract import AbstractReconfigCriterion

class NeverReconfigCriterion(AbstractReconfigCriterion):
    def reset(self):
        pass

    def update(self, session):
        pass
        
    def should_reconfigure(self):
        return False