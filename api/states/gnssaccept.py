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
            if packet.isSyn():
                context.ack = packet.ack + 1
                context.destAddrPort = recvingPacket.addrPort
                synAck = HUDPPacket.create(context.seq, context.ack, bytes(), isReliable=True, isSyn=True, isAck=True)
                context.seq += 1
                context.sendWindow.put(SendingHUDPPacket(synAck))
                return GNSStateSynRcvd()
            elif packet.isSynAck():
                rst = HUDPPacket.create(0, 0, bytes(), isRst=True)
                context.sendWindow.put(SendingHUDPPacket(rst))

        return self