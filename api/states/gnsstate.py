from __future__ import annotations
from abc import ABC, abstractmethod
from api.gnscontext import GNSContext


class GNSState(ABC):
    """
    Interface for a GameNetSocket state.
    """

    @abstractmethod
    def process(self, context: GNSContext) -> GNSState:
        pass
