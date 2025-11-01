from api.states.gnsstate import GNSState
from api.states.gnssestablished import GNSStateEstablished
from api.states.gnsssynrcvd import GNSStateSynRcvd
from api.states.gnssinitial import GNSStateInitial
from api.gnscontext import GNSContext, SendingHUDPPacket
from hudp import HUDPPacket


class GNSStateSynSent(GNSState):
    """
    SYN_SENT happens after user calls connect() on the socket.

    In this state, the socket (1) waits for the expected SYN ACK to come, send back the appropriate ACK
    and transition into ESTABLISHED, (2) waits for SYN packet from remote, notice the simultaneous open,
    send back SYN ACK and transition into SYN_RCVD or (3) terminates if a RST packet arrives from remote.

    All other packets are dropped and ignored.
    """

    def process(self, context: GNSContext) -> GNSState:
        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
            if packet.isSynAck() and packet.ack == context.seq:
                context.ack = packet.seq + 1
                context.rec = packet.ack
                ack = HUDPPacket.create(context.seq, context.ack, bytes(), isAck=True)
                context.sendWindow.put(SendingHUDPPacket(ack))
                context.connectSemaphore.release()
                return GNSStateEstablished()
            elif packet.isSyn():  # Simultaneous open
                context.ack = packet.ack + 1
                synAck = HUDPPacket.create(context.seq, context.ack, bytes(), isReliable=True, isSyn=True, isAck=True)
                context.seq += 1
                context.sendWindow.put(SendingHUDPPacket(synAck))
                return GNSStateSynRcvd()
            elif packet.isRst() and packet.ack == context.seq:
                return GNSStateInitial()

        return self
