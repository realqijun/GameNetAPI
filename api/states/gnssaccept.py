from api.states.gnsstate import GNSState
from api.states.gnsssynrcvd import GNSStateSynRcvd
from api.gnscontext import GNSContext, SendingHUDPPacket
from hudp import HUDPPacket


class GNSStateAccept(GNSState):
    """
    ACCEPT happens after user call accept() on the socket.

    In this state, the socket processes the first valid SYN packet that is sent to it
    and attempts to establish a connection with the remote that sent the SYN packet.

    After processing the first valid SYN packet and sending back the SYN_ACK packet,
    the state will change to SYN_RCVD.

    All other packets are dropped and ignored.
    """

    def process(self, context: GNSContext) -> GNSState:
        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
            if packet.isSyn():
                # Set ACK to remote's SEQ
                context.ack = packet.seq + 1
                context.destAddrPort = recvingPacket.addrPort
                # Send back SYN ACK, completing the 2nd step in the 3-way handshake
                synAck = HUDPPacket.create(context.seq, context.ack, isReliable=True, isSyn=True, isAck=True)
                context.seq += 1
                context.sendBuffer.put(SendingHUDPPacket(synAck))
                return GNSStateSynRcvd()

        return self
