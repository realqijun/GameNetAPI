from gnsstate import GNSState
from gnscontext import GNSContext
from common import AddrPort
from gnscontext import RecvingHUDPPacket, SendingHUDPPacket
from protocol.hudp import HUDPPacket


class GNSStateListen(GNSState):
    def __routine(self, context: GNSContext) -> GNSState:
        recvingPacket = context.recvWindow.get()
        packet = recvingPacket.packet
        synAck = HUDPPacket.create(self.seq, packet.seq + 1, bytes(), isReliable=True, isSyn=True, isAck=True)
        context.tempDestAddrPort = recvingPacket.addrPort
        context.sendWindow.put(SendingHUDPPacket(synAck))
        return self

    def __recv(self, context: GNSContext, data: bytes, addrPort: AddrPort):
        packet = HUDPPacket.fromBytes(data)
        if packet.flags.isSyn and not packet.flags.isAck:
            context.recvWindow.put(RecvingHUDPPacket(packet, addrPort))
