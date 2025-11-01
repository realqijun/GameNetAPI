from api.states.gnsstate import GNSState
from api.gnscontext import GNSContext
from api.states.gnssterminated import GNSStateTerminated


class GNSStateLastAck(GNSState):
    def process(self, context: GNSContext) -> GNSState:
        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
            if packet.isPureAck() and packet.ack == context.seq:
                context.rec = packet.ack
                context.closeSemaphore.release()
                return GNSStateTerminated()
            elif packet.isPureAck():
                context.rec = max(context.rec, packet.ack)

        return self