from api.states.gnsstate import GNSState
from api.gnscontext import GNSContext, SendingHUDPPacket
from api.states.gnssterminated import GNSStateTerminated
from hudp import HUDPPacket


class GNSStateCloseWait(GNSState):
    """
    CLOSE_WAIT happens after receiving FIN packets from remote and sending back the corresponding ACK.

    In this state, the socket (1) waits for duplicate FIN from remote and send back the appropriate ACK,
    (2) updates largest ACK received from remote if a pure ACK packet arrives or (3) terminates if a RST
    packet arrives from remote.

    To move on, user must call close() on the socket, which changes the state to LAST_ACK.

    All other packets are dropped and ignored.
    """

    def process(self, context: GNSContext) -> GNSState:
        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
            if packet.isFin() and packet.seq + 1 == context.ack:
                ack = HUDPPacket.create(context.seq, context.ack, bytes(), isAck=True)
                context.sendWindow.put(SendingHUDPPacket(ack))
            elif packet.isPureAck():
                context.rec = max(context.rec, packet.ack)
            elif packet.isRst():
                return GNSStateTerminated()

        return self
