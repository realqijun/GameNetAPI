from api.states.gnsstate import GNSState
from api.states.gnsssynrcvd import GNSStateSynRcvd
from api.gnscontext import GNSContext, SendingHUDPPacket
from hudp import HUDPPacket


class GNSStateAccept(GNSState):
    def process(self, context: GNSContext) -> GNSState:
        recvLen = context.recvWindow.qsize()
        for _ in range(recvLen):
            recvingPacket = context.recvWindow.get()
            packet = recvingPacket.packet
            if packet.isPureSyn():
                context.ack = packet.seq + 1
                context.destAddrPort = recvingPacket.addrPort
                synAck = HUDPPacket.create(context.seq, context.ack, bytes(), isReliable=True, isSyn=True, isAck=True)
                context.seq += 1
                context.sendWindow.put(SendingHUDPPacket(synAck))
                return GNSStateSynRcvd()

        return self