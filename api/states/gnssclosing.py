from api.states.gnsstate import GNSState
from api.gnscontext import GNSContext
from api.states.gnsstimewait import GNSStateTimeWait


class GNSStateClosing(GNSState):
    """
    CLOSING happens during a simultaneous close, when a FIN packet is sent out and a FIN packet is received
    from remote before the expected ACK.

    In this state, the socket waits for the expected ACK to come and transition into TIME_WAIT.

    All other packets are dropped and ignored.
    """

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
