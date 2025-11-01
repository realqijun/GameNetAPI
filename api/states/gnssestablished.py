from api.states.gnsstate import GNSState
from api.gnscontext import GNSContext, SendingHUDPPacket, RecvingHUDPPacket


class GNSStateEstablished(GNSState):
    def process(self, context: GNSContext) -> GNSState:
        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
        return self