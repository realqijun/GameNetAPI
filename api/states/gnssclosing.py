from api.states.gnsstate import GNSState
from api.gnscontext import GNSContext
from api.states.gnsstimewait import GNSStateTimeWait


class GNSStateClosing(GNSState):
    def process(self, context: GNSContext) -> GNSState:
        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
            if packet.isPureAck() and packet.ack == context.seq:
                context.rec = packet.ack
                context.closeSemaphore.release()
                return GNSStateTimeWait()

        return self