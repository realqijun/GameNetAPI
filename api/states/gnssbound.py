from api.states.gnsstate import GNSState
from api.gnscontext import GNSContext


class GNSStateBound(GNSState):
    """
    BOUND happens after user call bind() on the socket.

    To move on, user must call listen() or connect() on the socket, which changes the state to
    LISTEN or SYN_SENT respectively.

    In this state, nothing happens as packets are not being sent or received yet.
    """

    def process(self, context: GNSContext) -> GNSState:
        return self
