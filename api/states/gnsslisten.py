from api.states.gnsstate import GNSState
from api.gnscontext import GNSContext


class GNSStateListen(GNSState):
    """
    LISTEN happens after user calls listen() on the socket.

    To move on, user must call accept() or connect(), which changes the state to ACCEPT or SYN_SENT.

    In this state, nothing happens in the logic as only packets are received.
    """

    def process(self, context: GNSContext) -> GNSState:
        return self
