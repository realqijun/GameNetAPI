from api.states.gnssclosewait import GNSStateCloseWait
from api.states.gnsstate import GNSState
from api.states.gnssestablished import GNSStateEstablished
from api.gnscontext import GNSContext


class GNSStateSynRcvd(GNSState):
    def process(self, context: GNSContext) -> GNSState:
        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
            if packet.isAck() and packet.ack == context.seq:
                context.rec = packet.ack
                context.acceptSemaphore.release()
                return GNSStateEstablished()
            elif packet.isRst() and packet.ack == context.seq:
                from api.states.gnssaccept import GNSStateAccept
                return GNSStateAccept()
            elif packet.isFin() and packet.ack == context.seq:
                return GNSStateCloseWait()

        return self
