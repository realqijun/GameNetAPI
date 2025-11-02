from api.states.gnsstate import GNSState
from api.states.gnssestablished import GNSStateEstablished
from api.gnscontext import GNSContext


class GNSStateSynRcvd(GNSState):
    """
    SYN_RCVD happens after the ACCEPT state, when SYN ACK packet has been sent to remote.

    In this state, the socket (1) waits for the expected ACK and transition into ESTABLISHED,
    (2) waits for SYN ACK and transition into ESTABLISHED (simultaneous open)
    or (3) transition back to ACCEPT if a RST packet arrives from remote.

    All other packets are dropped and ignored.
    """

    def process(self, context: GNSContext) -> GNSState:
        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
            if packet.isPureAck() and packet.ack == context.seq:
                context.rec = packet.ack
                # Both active or passive open can go here
                context.acceptSemaphore.release()
                context.connectSemaphore.release()
                return GNSStateEstablished()
            elif packet.isSynAck() and packet.ack == context.seq:
                context.ack = packet.seq + 1
                context.rec = packet.ack
                context.connectSemaphore.release()
                return GNSStateEstablished()
            elif packet.isRst() and packet.ack == context.seq:
                from api.states.gnssaccept import GNSStateAccept
                return GNSStateAccept()

        return self
