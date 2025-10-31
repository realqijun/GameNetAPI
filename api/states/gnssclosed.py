from gnsstate import GNSState
from gnscontext import GNSContext
from common import AddrPort


class GNSStateClosed(GNSState):
    def __routine(self, context: GNSContext) -> GNSState:
        return self

    def __recv(self, context: GNSContext, packet: bytes, addrPort: AddrPort):
        pass
