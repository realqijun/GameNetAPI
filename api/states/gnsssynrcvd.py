from gnsstate import GNSState
from gnscontext import GNSContext
from common import AddrPort
from gnscontext import RecvingHUDPPacket
from protocol.hudp import HUDPPacket


class GNSStateSynRcvd(GNSState):
    def __routine(self, context: GNSContext) -> GNSState:
        recvingPacket = context.recvWindow.get()
        context.acceptQueue.put(context.tempDestAddrPort)
        context.ack = recvingPacket.packet.
        return self

    def __recv(self, context: GNSContext, data: bytes, addrPort: AddrPort):
        packet = HUDPPacket.fromBytes(data)
        if packet.flags.isAck and packet.ack == context.seq + 1 and context.tempDestAddrPort == addrPort:
            context.recvWindow.put(RecvingHUDPPacket(packet, addrPort))
