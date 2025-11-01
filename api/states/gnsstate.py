from __future__ import annotations
from abc import ABC, abstractmethod
from api.gnscontext import GNSContext


class GNSState(ABC):
    @abstractmethod
    def process(self, context: GNSContext) -> GNSState:
        pass
