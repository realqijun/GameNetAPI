from api.states.gnsstate import GNSState
from api.gnscontext import GNSContext


class GNSStateTerminated(GNSState):
    """
    TERMINATES is the final state of a socket, after a connection is closed on both sides.

    In this state, nothing happens as packets are not being sent or received yet.
    """

    def process(self, context: GNSContext) -> GNSState:
        return self
