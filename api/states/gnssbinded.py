from api.states.gnsstate import GNSState
from api.gnscontext import GNSContext


class GNSStateBinded(GNSState):
    def process(self, context: GNSContext) -> GNSState:
        return self
