from abc import ABC, abstractmethod
from typing import Dict, Any

class AbstractReconfigCriterion(ABC):
    def __init__(self, reset_every_reconfig: bool = True):
        self.reset()
        self.reset_every_reconfig = reset_every_reconfig
    
    @abstractmethod
    def reset(self):
        ...

    @abstractmethod
    def update(self, session: Dict[str, Any]):
        ...

    @abstractmethod
    def should_reconfigure(self) -> bool:
        ...