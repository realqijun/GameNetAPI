from __future__ import annotations
from abc import ABC, abstractmethod
from gnscontext import GNSContext


class GNSState(ABC):
    @abstractmethod
    def __routine(self, context: GNSContext) -> GNSState:
        pass

    @abstractmethod
    def __recv(self, context: GNSContext, packet: bytes):
        pass
