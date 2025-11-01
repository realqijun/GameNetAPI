from api.states.gnsstate import GNSState
from api.gnscontext import GNSContext


class GNSStateTerminated(GNSState):
    def process(self, context: GNSContext) -> GNSState:
        return self