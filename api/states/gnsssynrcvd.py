from api.states.gnsstate import GNSState
from api.states.gnssestablished import GNSStateEstablished
from api.gnscontext import GNSContext


class GNSStateSynRcvd(GNSState):
    """
    SYN_RCVD happens after the ACCEPT state, when SYN ACK packet has been sent to remote.

    In this state, the socket (1) waits for the expected ACK or SYN ACK to come and transition
    into ESTABLISHED or (2) transition back to ACCEPT if a RST packet arrives from remote.

    All other packets are dropped and ignored.
    """

    def process(self, context: GNSContext) -> GNSState:
        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
            if packet.isPureAck() and packet.ack == context.seq:
                context.rec = packet.ack
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
