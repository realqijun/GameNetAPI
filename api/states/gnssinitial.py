from api.states.gnsstate import GNSState
from api.gnscontext import GNSContext


class GNSStateInitial(GNSState):
    """
    INITIAL happens after user creates the socket.

    To move on, user must call bind(), which changes the state to BOUND that allows further operations.

    In this state, nothing happens as packets are not being sent or received yet.
    """

    def process(self, context: GNSContext) -> GNSState:
        return self
