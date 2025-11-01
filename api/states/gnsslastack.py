from api.states.gnsstate import GNSState
from api.gnscontext import GNSContext
from api.states.gnssterminated import GNSStateTerminated


class GNSStateLastAck(GNSState):
    """
    LAST_ACK happens after the CLOSE_WAIT state,
    when user calls close() and the remote send buffer is also closed.

    In this state, the socket (1) updates largest ACK received from remote if a pure ACK packet arrives
    and (2) waits for the expected ACK to come and transition into TERMINATED.

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
                return GNSStateTerminated()
            elif packet.isPureAck():
                context.rec = max(context.rec, packet.ack)

        return self
